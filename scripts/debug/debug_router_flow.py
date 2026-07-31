import asyncio

from app.bot.handlers.admin import admin_courier_flow
from app.bot.handlers.manager import manager_order_flow


class FakeState:
    async def get_state(self):
        return None

    async def set_state(self, state):
        self.state = state

    async def update_data(self, **kwargs):
        self.data = kwargs

    async def clear(self):
        self.state = None


class FakeMessage:
    def __init__(self):
        self.text = "📦 Створити заявку"
        self.from_user = type("U", (), {"id": 1})()
        self.replies = []

    async def answer(self, text, **kwargs):
        self.replies.append(text)


async def main():
    state = FakeState()
    msg = FakeMessage()
    print("admin-handler-start")
    await admin_courier_flow(msg, state)
    print("admin-handler-finished")
    print("manager-handler-start")
    await manager_order_flow(msg, state)
    print("manager-handler-finished")
    print("message-replies", msg.replies)


asyncio.run(main())
