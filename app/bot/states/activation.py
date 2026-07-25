from aiogram.fsm.state import State, StatesGroup


class ActivationState(StatesGroup):
    waiting_for_code = State()