from aiogram.fsm.state import State, StatesGroup


class ManagerOrderState(StatesGroup):
    waiting_for_destination_store = State()
    waiting_for_description = State()
    waiting_for_weight = State()
    waiting_for_priority = State()
