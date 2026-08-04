from aiogram.fsm.state import State, StatesGroup


class SetLocationStates(StatesGroup):
    location = State()
    coordinate = State()
    address = State()
