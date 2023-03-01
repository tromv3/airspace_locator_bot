from telebot import types
from telebot.types import InlineKeyboardMarkup


def keyboard_plane(plane: set) -> InlineKeyboardMarkup:
    """
    Функция для создания кнопок со ссылкой сайт (https://skybrary.aero/aircraft)
    для получения подробной информации по воздушному судну.

    :return: InlineKeyboardMarkup

    """

    markup = types.InlineKeyboardMarkup(row_width=2)
    for air in plane:
        markup.add(types.InlineKeyboardButton(f"Cамолет: {air}", url=f"https://skybrary.aero/aircraft/{air}"))
    return markup
