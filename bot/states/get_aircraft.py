from aiogram.fsm.state import State, StatesGroup


class GetAircraftStates(StatesGroup):
    dist = State()
    filters = State()
