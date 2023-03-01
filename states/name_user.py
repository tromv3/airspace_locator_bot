from telebot.handler_backends import State, StatesGroup


class ChangeNameState(StatesGroup):
    """
    Класс ChangeNameState.
    Состояния для изменения имени пользователя.

    """
    name = State()
