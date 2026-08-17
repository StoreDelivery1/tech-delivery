from aiogram.fsm.state import State, StatesGroup


class AdminCourierState(StatesGroup):
    waiting_for_full_name = State()


class AdminManagerState(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_network = State()
    waiting_for_store_query = State()
    waiting_for_store_selection = State()


class AdminOrderSearchState(StatesGroup):
    waiting_for_search_query = State()

