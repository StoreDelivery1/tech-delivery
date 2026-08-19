from aiogram.fsm.state import State, StatesGroup


class ProductOrderState(StatesGroup):
    waiting_for_source_store = State()
    waiting_for_description = State()
    waiting_for_size = State()
    waiting_for_confirmation = State()