import unittest

from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.manager import router as manager_router
from app.bot.handlers.product_order import (
    build_product_confirmation_keyboard,
    build_product_size_keyboard,
    format_product_confirmation,
    router as product_order_router,
)
from app.bot.states.admin import AdminManagerState
from app.models.order import OrderSize


class FakeState:
    def __init__(self):
        self._state = None
        self.data = {}

    async def get_state(self):
        return self._state

    async def set_state(self, state):
        self._state = state

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def clear(self):
        self._state = None

    async def get_data(self):
        return self.data


class FakeMessage:
    def __init__(self, text):
        self.text = text
        self.from_user = type("User", (), {"id": 1})()
        self.replies = []

    async def answer(self, text, **kwargs):
        self.replies.append(text)


class TestAdminRouterFlow(unittest.TestCase):
    def test_router_imports(self):
        self.assertIsNotNone(admin_router)
        self.assertIsNotNone(manager_router)
        self.assertIsNotNone(product_order_router)

    def test_product_order_size_keyboard_uses_existing_enum_values(self):
        keyboard = build_product_size_keyboard()
        callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
        self.assertEqual(callbacks, ["product_size:SMALL", "product_size:MEDIUM", "product_size:LARGE"])
        self.assertEqual({OrderSize[key.split(":")[1]] for key in callbacks}, set(OrderSize))

    def test_product_order_confirmation_contains_route_and_description(self):
        source = type("Store", (), {"network": "APPLE_ROOM", "name": "Source"})()
        destination = type("Store", (), {"network": "JABKO", "name": "Destination"})()
        text = format_product_confirmation({
            "source_store": source,
            "destination_store": destination,
            "description": "2 iPhone 16 Pro",
            "size": OrderSize.SMALL,
        })
        self.assertIn("Звідки", text)
        self.assertIn("Куди", text)
        self.assertIn("2 iPhone 16 Pro", text)
        self.assertIn("Розмір:</b> Мале", text)
        self.assertEqual(len(build_product_confirmation_keyboard().inline_keyboard[0]), 2)

    def test_manager_state_exists(self):
        self.assertTrue(hasattr(AdminManagerState, "waiting_for_full_name"))
        self.assertTrue(hasattr(AdminManagerState, "waiting_for_network"))
        self.assertTrue(hasattr(AdminManagerState, "waiting_for_store_query"))
        self.assertTrue(hasattr(AdminManagerState, "waiting_for_store_selection"))


if __name__ == "__main__":
    unittest.main()
