from aiogram.fsm.state import State, StatesGroup


class GetAircraftStates(StatesGroup):
    dist = State()
    filters = State()
    filter_alt = State()
    filter_flag = State()
    filter_type = State()
