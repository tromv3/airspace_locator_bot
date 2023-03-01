from telebot.handler_backends import State, StatesGroup


class SetLocationState(StatesGroup):
    location = State()
    coordinate = State()
    address = State()
