from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Изменить местоположение")
    builder.button(text="Получить данные о воздушных судах")
    builder.button(text="Повторить последний поиск")
    builder.button(text="Отрисовать полученные данные")
    builder.button(text="Подробно о воздушном судне")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def address_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Ввести адрес")
    builder.button(text="Ввести координаты")
    builder.button(text="Отправить свое местоположение", request_location=True)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)
