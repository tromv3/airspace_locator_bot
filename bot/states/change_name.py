from aiogram.fsm.state import State, StatesGroup


class ChangeNameStates(StatesGroup):
    name = State()
