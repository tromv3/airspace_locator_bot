from telebot import types
from telebot.types import ReplyKeyboardMarkup


def keyboard_start() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_ch_user = types.KeyboardButton(text="Изменить имя")
    button_address = types.KeyboardButton(text="Изменить местоположение")
    button_aircraft = types.KeyboardButton(text="Получить данные о воздушных судах")
    button_info = types.KeyboardButton(text="Подробно о воздушном судне")
    button_draw = types.KeyboardButton(text="Отрисовать полученные данные")
    markup.add(button_ch_user, button_address, button_aircraft, button_draw, button_info)
    return markup
