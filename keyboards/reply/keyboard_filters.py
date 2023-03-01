from telebot import types
from telebot.types import ReplyKeyboardMarkup


def keyboard_filters() -> ReplyKeyboardMarkup:
    """
    Функция для создания клавиатуры (клавиатура для выбора фильтра)

    :return: ReplyKeyboardMarkup

    """

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_alt_max = types.KeyboardButton(text="Фильтр по высоте (max)")
    button_alt_min = types.KeyboardButton(text="Фильтр по высоте (min)")
    button_type = types.KeyboardButton(text="Фильтр по типу")
    button_flag = types.KeyboardButton(text="Фильтр по принадлежности")
    button_save = types.KeyboardButton(text="Показать воздушные суда")
    markup.add(button_alt_max, button_alt_min, button_type, button_flag, button_save)
    return markup
