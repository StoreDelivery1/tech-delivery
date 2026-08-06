import asyncio
import unittest
from unittest.mock import patch

from app.bot.handlers.start import start_handler
from app.models.user import User, UserRole, UserStatus


class _FakeDb:
    def close(self):
        return None


class _FakeState:
    def __init__(self):
        self.cleared = False

    async def clear(self):
        self.cleared = True

    async def set_state(self, state):
        return None


class _FakeMessage:
    def __init__(self, user_id: int, username: str = "user"):
        self.text = "/start"
        self.from_user = type("FromUser", (), {"id": user_id, "username": username})()
        self.answers: list[str] = []

    async def answer(self, text: str, **kwargs):
        self.answers.append(text)


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


if __name__ == "__main__":
    unittest.main()
