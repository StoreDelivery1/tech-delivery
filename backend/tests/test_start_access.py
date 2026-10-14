import asyncio
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.bot.handlers.start import start_handler
from app.database.base import Base
from app.models.store import Store, StoreNetwork
from app.models.user import CourierAvailability, User, UserRole, UserStatus


class _FakeDb:
    def close(self):
        return None


class _FakeState:
    def __init__(self):
        self.cleared = False
        self.state = None

    async def clear(self):
        self.cleared = True

    async def set_state(self, state):
        self.state = state


class _FakeMessage:
    def __init__(self, user_id: int, username: str = "user"):
        self.text = "/start"
        self.from_user = type("FromUser", (), {"id": user_id, "username": username})()
        self.answers: list[str] = []
        self.reply_markups = []

    async def answer(self, text: str, **kwargs):
        self.answers.append(text)
        self.reply_markups.append(kwargs.get("reply_markup"))


class TestStartAccess(unittest.TestCase):
    def test_inactive_user_gets_blocked_message(self):
        state = _FakeState()
        message = _FakeMessage(user_id=21)
        inactive_user = User(
            full_name="Inactive Employee",
            role=UserRole.COURIER,
            status=UserStatus.INACTIVE,
            telegram_id=21,
        )

        with patch("app.bot.handlers.start.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.handlers.start.ActivationService.get_by_telegram", return_value=inactive_user):
                asyncio.run(start_handler(message, state))

        self.assertTrue(state.cleared)
        self.assertIn("Ваш обліковий запис неактивний", message.answers[0])

    def test_active_user_keeps_access(self):
        state = _FakeState()
        message = _FakeMessage(user_id=22)
        active_admin = User(
            full_name="Active Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            telegram_id=22,
        )

        with patch("app.bot.handlers.start.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.handlers.start.ActivationService.get_by_telegram", return_value=active_admin):
                with patch("app.bot.handlers.start.ActivationService.update_last_login"):
                    asyncio.run(start_handler(message, state))

        self.assertTrue(any("Адміністратор" in text for text in message.answers))
        self.assertEqual(len(message.answers), 1)
        self.assertIsNotNone(message.reply_markups[0])
        self.assertTrue(any("Користувачі" in button.text for row in message.reply_markups[0].keyboard for button in row))

    def test_manager_gets_manager_menu(self):
        state = _FakeState()
        message = _FakeMessage(user_id=23)
        manager = User(
            full_name="Active Manager",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            telegram_id=23,
            store_id=1,
        )

        with patch("app.bot.handlers.start.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.handlers.start.ActivationService.get_by_telegram", return_value=manager):
                with patch("app.bot.handlers.start.ActivationService.update_last_login"):
                    with patch("app.bot.handlers.start.ManagerService.get_my_created_orders", return_value=([], [])):
                        asyncio.run(start_handler(message, state))

        self.assertIn("Менеджер", message.answers[0])
        self.assertEqual(len(message.answers), 1)
        self.assertTrue(any("Створити заявку" in button.text for row in message.reply_markups[0].keyboard for button in row))

    def test_courier_gets_courier_menu(self):
        state = _FakeState()
        message = _FakeMessage(user_id=24)
        courier = User(
            full_name="Active Courier",
            role=UserRole.COURIER,
            status=UserStatus.ACTIVE,
            telegram_id=24,
            availability=CourierAvailability.OFFLINE,
        )

        with patch("app.bot.handlers.start.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.handlers.start.ActivationService.get_by_telegram", return_value=courier):
                with patch("app.bot.handlers.start.ActivationService.update_last_login"):
                    asyncio.run(start_handler(message, state))

        self.assertIn("Кур'єр", message.answers[0])
        self.assertEqual(len(message.answers), 1)
        self.assertTrue(any("Вільні замовлення" in button.text for row in message.reply_markups[0].keyboard for button in row))

    def test_unknown_user_starts_activation_flow(self):
        state = _FakeState()
        message = _FakeMessage(user_id=25)

        with patch("app.bot.handlers.start.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.handlers.start.ActivationService.get_by_telegram", return_value=None):
                asyncio.run(start_handler(message, state))

        self.assertIsNotNone(state.state)
        self.assertIn("код активації", message.answers[0])
        self.assertEqual(len(message.answers), 1)

    def test_manager_without_store_is_denied(self):
        state = _FakeState()
        message = _FakeMessage(user_id=26)
        manager = User(
            full_name="Unassigned Manager",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            telegram_id=26,
        )

        with patch("app.bot.handlers.start.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.handlers.start.ActivationService.get_by_telegram", return_value=manager):
                asyncio.run(start_handler(message, state))

        self.assertIn("магазин не призначено", message.answers[0])
        self.assertIsNone(message.reply_markups[0])

    def test_unsupported_role_is_denied(self):
        state = _FakeState()
        message = _FakeMessage(user_id=27)
        seller = User(
            full_name="Employee",
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            telegram_id=27,
        )

        with patch("app.bot.handlers.start.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.handlers.start.ActivationService.get_by_telegram", return_value=seller):
                asyncio.run(start_handler(message, state))

        self.assertIn("не має доступу", message.answers[0])
        self.assertIsNone(message.reply_markups[0])

    def test_missing_role_is_reported(self):
        state = _FakeState()
        message = _FakeMessage(user_id=30)
        user_without_role = User(
            full_name="Employee Without Role",
            role=None,
            status=UserStatus.ACTIVE,
            telegram_id=30,
        )

        with patch("app.bot.handlers.start.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.handlers.start.ActivationService.get_by_telegram", return_value=user_without_role):
                asyncio.run(start_handler(message, state))

        self.assertIn("роль «не визначена»", message.answers[0])
        self.assertIsNone(message.reply_markups[0])

    def test_database_error_is_reported_without_crashing(self):
        state = _FakeState()
        message = _FakeMessage(user_id=28)

        with patch("app.bot.handlers.start.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.handlers.start.ActivationService.get_by_telegram", side_effect=RuntimeError("database unavailable")):
                asyncio.run(start_handler(message, state))

        self.assertIn("тимчасову помилку", message.answers[0])
        self.assertEqual(len(message.answers), 1)

    def test_manager_menu_is_sent_when_order_count_query_fails(self):
        state = _FakeState()
        message = _FakeMessage(user_id=29)
        manager = User(
            full_name="Active Manager",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            telegram_id=29,
            store_id=1,
        )

        with patch("app.bot.handlers.start.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.handlers.start.ActivationService.get_by_telegram", return_value=manager):
                with patch("app.bot.handlers.start.ActivationService.update_last_login"):
                    with patch("app.bot.handlers.start.ManagerService.get_my_created_orders", side_effect=RuntimeError("query failed")):
                        asyncio.run(start_handler(message, state))

        self.assertIn("Менеджер", message.answers[0])
        self.assertIsNotNone(message.reply_markups[0])
        self.assertEqual(len(message.answers), 1)

    def test_failed_count_query_does_not_poison_login_transaction(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        setup_db = session_factory()
        store = Store(
            name="Test Store",
            address="Address",
            city="Lviv",
            latitude=49.0,
            longitude=24.0,
            network=StoreNetwork.APPLE_ROOM,
        )
        setup_db.add(store)
        setup_db.commit()
        manager = User(
            full_name="Active Manager",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            telegram_id=31,
            store_id=store.id,
        )
        setup_db.add(manager)
        setup_db.commit()
        manager_id = manager.id
        setup_db.close()

        sessions = []

        def create_session():
            session = session_factory()
            sessions.append(session)
            return session

        def fail_counts(db, user_id):
            db.execute(text("SELECT * FROM missing_order_table"))

        state = _FakeState()
        message = _FakeMessage(user_id=31)
        with patch("app.bot.handlers.start.SessionLocal", side_effect=create_session):
            with patch("app.bot.handlers.start.ManagerService.get_my_created_orders", side_effect=fail_counts):
                asyncio.run(start_handler(message, state))

        self.assertEqual(len(sessions), 2)
        self.assertFalse(sessions[1].in_transaction())
        self.assertIn("Менеджер", message.answers[0])
        self.assertIsNotNone(message.reply_markups[0])

        verification_db = session_factory()
        persisted_manager = verification_db.get(User, manager_id)
        self.assertIsNotNone(persisted_manager.last_login_at)
        verification_db.close()
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
