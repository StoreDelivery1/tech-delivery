import asyncio
import unittest
from unittest.mock import Mock, patch

from app.bot.filters.roles import AdminFilter, CourierFilter, ManagerFilter
from app.models.user import User, UserRole, UserStatus


class _FakeDb:
    def close(self):
        return None


class _FakeMessage:
    def __init__(self, user_id: int):
        self.from_user = type("FromUser", (), {"id": user_id})()
        self.answers: list[str] = []

    async def answer(self, text: str, **kwargs):
        self.answers.append(text)


class _FakeCallback:
    def __init__(self, user_id: int):
        self.from_user = type("FromUser", (), {"id": user_id})()
        self.message = object()
        self.answers: list[tuple[str, bool]] = []

    async def answer(self, text: str, show_alert: bool = False, **kwargs):
        self.answers.append((text, show_alert))


class TestBotRoleFilters(unittest.TestCase):
    def test_active_telegram_user_has_manager_access(self):
        update = _FakeMessage(user_id=11)
        active_manager = User(
            full_name="Manager",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            telegram_id=11,
            store_id=1,
        )

        with patch("app.bot.filters.roles.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.filters.roles.ActivationService.get_by_telegram", return_value=active_manager):
                with patch("app.bot.filters.roles.ActivationService.get_manager", return_value=active_manager):
                    allowed = asyncio.run(ManagerFilter().__call__(update))

        self.assertTrue(allowed)
        self.assertEqual(update.answers, [])

    def test_active_manager_without_store_is_denied_with_message(self):
        update = _FakeMessage(user_id=16)
        manager_without_store = User(
            full_name="Manager",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            telegram_id=16,
        )

        with patch("app.bot.filters.roles.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.filters.roles.ActivationService.get_by_telegram", return_value=manager_without_store):
                with patch("app.bot.filters.roles.ActivationService.get_manager", return_value=manager_without_store):
                    allowed = asyncio.run(ManagerFilter().__call__(update))

        self.assertFalse(allowed)
        self.assertEqual(len(update.answers), 1)
        self.assertIn("не прив'язаний до магазину", update.answers[0])

    def test_manager_callback_without_store_is_denied_with_alert(self):
        callback = _FakeCallback(user_id=17)
        manager_without_store = User(
            full_name="Manager",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            telegram_id=17,
        )

        with patch("app.bot.filters.roles.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.filters.roles.ActivationService.get_by_telegram", return_value=manager_without_store):
                with patch("app.bot.filters.roles.ActivationService.get_manager", return_value=manager_without_store):
                    allowed = asyncio.run(ManagerFilter().__call__(callback))

        self.assertFalse(allowed)
        self.assertEqual(len(callback.answers), 1)
        self.assertIn("не прив'язаний до магазину", callback.answers[0][0])
        self.assertTrue(callback.answers[0][1])

    def test_non_manager_role_does_not_pass_manager_filter(self):
        update = _FakeMessage(user_id=18)
        courier = User(
            full_name="Courier",
            role=UserRole.COURIER,
            status=UserStatus.ACTIVE,
            telegram_id=18,
        )

        with patch("app.bot.filters.roles.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.filters.roles.ActivationService.get_by_telegram", return_value=courier):
                with patch("app.bot.filters.roles.ActivationService.get_manager", return_value=None):
                    allowed = asyncio.run(ManagerFilter().__call__(update))

        self.assertFalse(allowed)

    def test_inactive_manager_cannot_execute_manager_callback(self):
        callback = _FakeCallback(user_id=12)
        inactive_manager = User(
            full_name="Inactive Manager",
            role=UserRole.MANAGER,
            status=UserStatus.INACTIVE,
            telegram_id=12,
        )

        with patch("app.bot.filters.roles.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.filters.roles.ActivationService.get_by_telegram", return_value=inactive_manager):
                allowed = asyncio.run(ManagerFilter().__call__(callback))

        self.assertFalse(allowed)
        self.assertEqual(len(callback.answers), 1)
        self.assertEqual(
            callback.answers[0][0],
            "Ваш обліковий запис неактивний. Зверніться до адміністратора.",
        )
        self.assertTrue(callback.answers[0][1])

    def test_inactive_courier_cannot_execute_courier_callback(self):
        callback = _FakeCallback(user_id=13)
        inactive_courier = User(
            full_name="Inactive Courier",
            role=UserRole.COURIER,
            status=UserStatus.INACTIVE,
            telegram_id=13,
        )

        with patch("app.bot.filters.roles.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.filters.roles.ActivationService.get_by_telegram", return_value=inactive_courier):
                allowed = asyncio.run(CourierFilter().__call__(callback))

        self.assertFalse(allowed)
        self.assertEqual(len(callback.answers), 1)

    def test_inactive_admin_cannot_execute_admin_action(self):
        message = _FakeMessage(user_id=14)
        inactive_admin = User(
            full_name="Inactive Admin",
            role=UserRole.ADMIN,
            status=UserStatus.INACTIVE,
            telegram_id=14,
        )

        with patch("app.bot.filters.roles.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.filters.roles.ActivationService.get_by_telegram", return_value=inactive_admin):
                allowed = asyncio.run(AdminFilter().__call__(message))

        self.assertFalse(allowed)
        self.assertEqual(
            message.answers,
            ["Ваш обліковий запис неактивний. Зверніться до адміністратора."],
        )

    def test_reactivated_user_regains_access(self):
        update = _FakeMessage(user_id=15)
        inactive = User(
            full_name="Worker",
            role=UserRole.MANAGER,
            status=UserStatus.INACTIVE,
            telegram_id=15,
        )
        active = User(
            full_name="Worker",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            telegram_id=15,
            store_id=1,
        )

        with patch("app.bot.filters.roles.SessionLocal", return_value=_FakeDb()):
            with patch("app.bot.filters.roles.ActivationService.get_by_telegram", side_effect=[inactive, active]):
                with patch("app.bot.filters.roles.ActivationService.get_manager", return_value=active):
                    denied = asyncio.run(ManagerFilter().__call__(update))
                    allowed = asyncio.run(ManagerFilter().__call__(update))

        self.assertFalse(denied)
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()
