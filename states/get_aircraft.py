from telebot.handler_backends import State, StatesGroup


class GetAircraftState(StatesGroup):
    """
    Класс GetAircraftState.
    Состояния для получения информации о воздушных судах.

    """
    dist = State()
    filters = State()
    filter_alt = State()
    filter_flag = State()
    filter_type = State()
