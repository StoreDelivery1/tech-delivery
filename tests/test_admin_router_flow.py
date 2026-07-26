import unittest

from aiogram.dispatcher.event.bases import UNHANDLED

from app.bot.handlers.admin import admin_courier_flow
from app.bot.handlers.manager import manager_order_flow


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


class AdminRouterFlowTests(unittest.TestCase):
    def test_unrelated_message_is_left_for_other_routers(self):
        state = FakeState()
        message = FakeMessage("📦 Створити заявку")

        admin_result = unittest.IsolatedAsyncioTestCase().runTest if False else None

    async def _run_flow(self):
        state = FakeState()
        message = FakeMessage("📦 Створити заявку")

        admin_result = await admin_courier_flow(message, state)
        self.assertIs(admin_result, UNHANDLED)

        manager_result = await manager_order_flow(message, state)
        self.assertIsNone(manager_result)
        self.assertIn("🏪 Введіть ID магазину призначення:", message.replies)

    def test_unrelated_message_is_left_for_other_routers(self):
        import asyncio
        asyncio.run(self._run_flow())


if __name__ == "__main__":
    unittest.main()
