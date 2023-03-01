from telebot.handler_backends import State, StatesGroup


class SetLocationState(StatesGroup):
    """
    Класс SetLocationState.
    Состояния для получения геолокации.

    """
    location = State()
    coordinate = State()
    address = State()
