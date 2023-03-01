from telebot.handler_backends import State, StatesGroup


class ChangeNameState(StatesGroup):
    name = State()
