from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

SKYBRARY_URL_TEMPLATE = "https://skybrary.aero/aircraft/{code}"


def plane_info_keyboard(plane_types: set[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plane_type in sorted(plane_types):
        builder.button(
            text=f"Самолет: {plane_type}", url=SKYBRARY_URL_TEMPLATE.format(code=plane_type)
        )
    builder.adjust(2)
    return builder.as_markup()
