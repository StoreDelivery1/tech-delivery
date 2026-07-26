from aiogram.fsm.state import State, StatesGroup


class AdminCourierState(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_store = State()
