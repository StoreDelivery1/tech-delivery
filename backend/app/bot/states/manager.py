from aiogram.fsm.state import State, StatesGroup


class ManagerOrderState(StatesGroup):
    waiting_for_destination_store = State()
    waiting_for_description = State()
    waiting_for_size = State()
    waiting_for_priority = State()


class ManagerIncomingDeliveriesState(StatesGroup):
    viewing_list = State()
    viewing_detail = State()


class ManagerDeliveryConfirmationState(StatesGroup):
    confirming_delivery = State()
    reporting_problem = State()
