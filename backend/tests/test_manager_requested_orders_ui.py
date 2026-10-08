import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.bot.handlers.manager import (
    _build_requested_order_detail_keyboard,
    _build_requested_order_detail_message,
    _build_requested_orders_keyboard,
    incoming_deliveries_handler,
    requested_order_detail_callback,
    requested_order_transfer_callback,
    requested_orders_handler,
    requested_orders_page_callback,
)
from app.bot.keyboards.main_menu import manager_main_menu
from app.models.order import OrderStatus
from app.models.store import StoreNetwork


class FakeMessage:
    def __init__(self):
        self.from_user = SimpleNamespace(id=9001)
        self.answers = []
        self.edits = []

    async def answer(self, text, **kwargs):
        self.answers.append((text, kwargs))

    async def edit_text(self, text, **kwargs):
        self.edits.append((text, kwargs))


class FakeCallback:
    def __init__(self, data):
        self.data = data
        self.from_user = SimpleNamespace(id=9001)
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, **kwargs):
        self.answers.append((text, kwargs))


class TestManagerRequestedOrdersUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = Mock()
        self.manager = SimpleNamespace(id=71, store_id=1)
        self.requester_store = SimpleNamespace(
            id=2,
            name="Форум",
            network=StoreNetwork.JABKO,
        )
        self.order = SimpleNamespace(
            id=125,
            from_store_id=1,
            to_store_id=2,
            to_store=self.requester_store,
            creator=SimpleNamespace(store_id=2),
            courier_id=None,
            description="iPhone 17 Pro Max 256GB — 1 шт.",
            status=OrderStatus.WAITING_FOR_COURIER,
            created_at=datetime(2026, 10, 6, 12, 30),
        )

    def _detail_keyboard_button_texts(self, order=None, manager=None):
        keyboard = _build_requested_order_detail_keyboard(
            order or self.order,
            manager or self.manager,
        )
        return [button.text for row in keyboard.inline_keyboard for button in row]

    def test_manager_menu_has_requested_button_next_to_incoming(self):
        menu = manager_main_menu()
        rows = [[button.text for button in row] for row in menu.keyboard]

        row = next(row for row in rows if any(text.startswith("📥 До нас їдуть") for text in row))
        self.assertEqual(row, ["📥 До нас їдуть (0)", "📦 Замовили"])

    async def test_manager_sees_requested_orders_list(self):
        message = FakeMessage()
        with (
            patch("app.bot.handlers.manager.SessionLocal", return_value=self.db),
            patch("app.bot.handlers.manager.ActivationService.get_manager", return_value=self.manager),
            patch(
                "app.bot.handlers.manager.ManagerService.get_active_orders_requested_from_store",
                return_value=[self.order],
            ) as get_orders,
        ):
            await requested_orders_handler(message)

        get_orders.assert_called_once_with(self.db, self.manager.id)
        text, kwargs = message.answers[0]
        self.assertIn("📦 Замовили", text)
        self.assertIn("🍎 Ябко — Форум", text)
        self.assertIn("iPhone 17 Pro Max 256GB — 1 шт.", text)
        self.assertIn("#125", text)
        callbacks = [
            button.callback_data
            for row in kwargs["reply_markup"].inline_keyboard
            for button in row
        ]
        self.assertIn("manager_requested_detail:125", callbacks)

    async def test_empty_state_message(self):
        message = FakeMessage()
        with (
            patch("app.bot.handlers.manager.SessionLocal", return_value=self.db),
            patch("app.bot.handlers.manager.ActivationService.get_manager", return_value=self.manager),
            patch("app.bot.handlers.manager.ManagerService.get_active_orders_requested_from_store", return_value=[]),
        ):
            await requested_orders_handler(message)

        self.assertEqual(message.answers[0][0], "📦 Замовили\n\nНемає активних замовлень.")

    async def test_detail_uses_service_method_and_shows_requested_order(self):
        callback = FakeCallback("manager_requested_detail:125")
        with (
            patch("app.bot.handlers.manager.SessionLocal", return_value=self.db),
            patch("app.bot.handlers.manager.ActivationService.get_manager", return_value=self.manager),
            patch(
                "app.bot.handlers.manager.ManagerService.get_active_order_requested_from_store",
                return_value=self.order,
            ) as get_order,
        ):
            await requested_order_detail_callback(callback)

        get_order.assert_called_once_with(self.db, self.manager.id, 125)
        text, kwargs = callback.message.edits[0]
        self.assertIn("📦 <b>Замовлення #125</b>", text)
        self.assertIn("Від:\n🍎 Ябко — Форум", text)
        self.assertIn("iPhone 17 Pro Max 256GB — 1 шт.", text)
        self.assertIn("Статус:\nОчікує кур'єра", text)
        self.assertIn("06.10.2026 12:30", text)
        self.assertEqual(
            kwargs["reply_markup"].inline_keyboard[0][0].callback_data,
            "manager_requested_orders:0",
        )

    def test_transfer_button_shown_for_accepted_product_order_with_courier(self):
        self.order.status = OrderStatus.ACCEPTED
        self.order.courier_id = 88

        self.assertIn("📦 Передати товар", self._detail_keyboard_button_texts())

    def test_transfer_button_hidden_for_product_order_waiting_for_courier(self):
        self.order.courier_id = 88

        self.assertNotIn("📦 Передати товар", self._detail_keyboard_button_texts())

    def test_transfer_button_hidden_for_product_order_without_courier(self):
        self.order.status = OrderStatus.ACCEPTED

        self.assertNotIn("📦 Передати товар", self._detail_keyboard_button_texts())

    def test_transfer_button_hidden_for_product_order_already_picked_up(self):
        self.order.status = OrderStatus.PICKED_UP
        self.order.courier_id = 88

        self.assertNotIn("📦 Передати товар", self._detail_keyboard_button_texts())

    def test_transfer_button_hidden_for_all_later_statuses(self):
        self.order.courier_id = 88
        for status in (
            OrderStatus.DELIVERING,
            OrderStatus.AWAITING_CONFIRMATION,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELED,
        ):
            with self.subTest(status=status):
                self.order.status = status
                self.assertNotIn("📦 Передати товар", self._detail_keyboard_button_texts())

    def test_transfer_button_hidden_for_regular_order(self):
        self.order.status = OrderStatus.ACCEPTED
        self.order.courier_id = 88
        self.order.creator.store_id = self.order.from_store_id

        self.assertNotIn("📦 Передати товар", self._detail_keyboard_button_texts())

    def test_foreign_product_order_has_no_transfer_button(self):
        self.order.status = OrderStatus.ACCEPTED
        self.order.courier_id = 88
        foreign_manager = SimpleNamespace(id=72, store_id=99)

        self.assertNotIn(
            "📦 Передати товар",
            self._detail_keyboard_button_texts(manager=foreign_manager),
        )

    async def test_transfer_callback_calls_service_and_shows_success_and_list_button(self):
        callback = FakeCallback("manager_requested_transfer:125")
        self.order.status = OrderStatus.ACCEPTED
        self.order.courier_id = 88
        with (
            patch("app.bot.handlers.manager.SessionLocal", return_value=self.db),
            patch("app.bot.handlers.manager.ActivationService.get_manager", return_value=self.manager),
            patch(
                "app.bot.handlers.manager.ManagerService.transfer_requested_product_order_to_courier",
                return_value=self.order,
            ) as transfer_order,
        ):
            await requested_order_transfer_callback(callback)

        transfer_order.assert_called_once_with(self.db, self.manager.id, 125)
        self.assertEqual(callback.message.edits[0][0], "✅ Товар передано кур'єру.")
        button = callback.message.edits[0][1]["reply_markup"].inline_keyboard[0][0]
        self.assertEqual(button.text, "⬅️ До замовлень")
        self.assertEqual(button.callback_data, "manager_requested_orders:0")
        self.assertEqual(callback.answers[-1], (None, {}))

    async def test_transfer_callback_maps_service_errors_without_exposing_traceback(self):
        cases = (
            ("Only accepted orders can be transferred to the courier", "вже передано"),
            ("Order has no assigned courier", "не призначено кур'єра"),
            ("Order does not belong to the manager's store", "Недостатньо прав"),
            ("Order not found", "не знайдено"),
        )
        for error, expected_message in cases:
            callback = FakeCallback("manager_requested_transfer:125")
            with (
                patch("app.bot.handlers.manager.SessionLocal", return_value=self.db),
                patch("app.bot.handlers.manager.ActivationService.get_manager", return_value=self.manager),
                patch(
                    "app.bot.handlers.manager.ManagerService.transfer_requested_product_order_to_courier",
                    side_effect=ValueError(error),
                ) as transfer_order,
            ):
                with self.subTest(error=error):
                    await requested_order_transfer_callback(callback)

            transfer_order.assert_called_once_with(self.db, self.manager.id, 125)
            self.assertIn(expected_message, callback.answers[0][0])
            self.assertEqual(callback.message.edits, [])

    async def test_successful_transfer_back_to_list_shows_refreshed_empty_state(self):
        transfer_callback = FakeCallback("manager_requested_transfer:125")
        with (
            patch("app.bot.handlers.manager.SessionLocal", return_value=self.db),
            patch("app.bot.handlers.manager.ActivationService.get_manager", return_value=self.manager),
            patch(
                "app.bot.handlers.manager.ManagerService.transfer_requested_product_order_to_courier",
                return_value=self.order,
            ),
        ):
            await requested_order_transfer_callback(transfer_callback)

        list_callback = FakeCallback("manager_requested_orders:0")
        with (
            patch("app.bot.handlers.manager.SessionLocal", return_value=self.db),
            patch("app.bot.handlers.manager.ActivationService.get_manager", return_value=self.manager),
            patch(
                "app.bot.handlers.manager.ManagerService.get_active_orders_requested_from_store",
                return_value=[],
            ) as get_orders,
        ):
            await requested_orders_page_callback(list_callback)

        get_orders.assert_called_once_with(self.db, self.manager.id)
        self.assertIn("Немає активних замовлень", list_callback.message.edits[0][0])
        self.assertNotIn("#125", list_callback.message.edits[0][0])

    async def test_foreign_or_missing_order_is_rejected_by_detail_service(self):
        callback = FakeCallback("manager_requested_detail:999")
        with (
            patch("app.bot.handlers.manager.SessionLocal", return_value=self.db),
            patch("app.bot.handlers.manager.ActivationService.get_manager", return_value=self.manager),
            patch("app.bot.handlers.manager.ManagerService.get_active_order_requested_from_store", return_value=None) as get_order,
        ):
            await requested_order_detail_callback(callback)

        get_order.assert_called_once_with(self.db, self.manager.id, 999)
        self.assertEqual(callback.message.edits, [])
        self.assertTrue(callback.answers[0][1]["show_alert"])

    async def test_list_pagination_callback_returns_requested_list(self):
        callback = FakeCallback("manager_requested_orders:0")
        with (
            patch("app.bot.handlers.manager.SessionLocal", return_value=self.db),
            patch("app.bot.handlers.manager.ActivationService.get_manager", return_value=self.manager),
            patch("app.bot.handlers.manager.ManagerService.get_active_orders_requested_from_store", return_value=[self.order]),
        ):
            await requested_orders_page_callback(callback)

        self.assertIn("📦 Замовили", callback.message.edits[0][0])

    async def test_existing_incoming_deliveries_empty_state_is_unchanged(self):
        message = FakeMessage()
        with (
            patch("app.bot.handlers.manager.SessionLocal", return_value=self.db),
            patch("app.bot.handlers.manager.ActivationService.get_manager", return_value=self.manager),
            patch("app.bot.handlers.manager.ManagerService.get_incoming_active_deliveries", return_value=[]) as get_incoming,
        ):
            await incoming_deliveries_handler(message)

        get_incoming.assert_called_once_with(self.db, self.manager.id)
        self.assertIn("📥 До нас їдуть", message.answers[0][0])
        self.assertIn("Зараз немає активних доставок", message.answers[0][0])


if __name__ == "__main__":
    unittest.main()