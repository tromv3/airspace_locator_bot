from telebot import types
from telebot.types import ReplyKeyboardMarkup


def keyboard_address() -> ReplyKeyboardMarkup:
    """
    Функция для создания клавиатуры (клавиатура для ввода адреса)

    :return: ReplyKeyboardMarkup

    """

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_s_address = types.KeyboardButton(text="Ввести адрес")
    button_s_coord = types.KeyboardButton(text="Ввести координаты")
    button_s_location = types.KeyboardButton(text="Отправить свое местоположение", request_location=True)
    markup.add(button_s_address, button_s_coord, button_s_location)
    return markup
