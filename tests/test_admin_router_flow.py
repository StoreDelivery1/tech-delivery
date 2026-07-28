import unittest

from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.manager import router as manager_router
from app.bot.states.admin import AdminManagerState


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
    def test_router_imports(self):
        self.assertIsNotNone(admin_router)
        self.assertIsNotNone(manager_router)

    def test_manager_state_exists(self):
        self.assertTrue(hasattr(AdminManagerState, "waiting_for_full_name"))
        self.assertTrue(hasattr(AdminManagerState, "waiting_for_network"))
        self.assertTrue(hasattr(AdminManagerState, "waiting_for_store_query"))
        self.assertTrue(hasattr(AdminManagerState, "waiting_for_store_selection"))


if __name__ == "__main__":
    unittest.main()
