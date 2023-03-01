from telebot.handler_backends import State, StatesGroup


class GetAircraftState(StatesGroup):
    dist = State()
    filters = State()
    filter_alt = State()
    filter_flag = State()
    filter_type = State()
