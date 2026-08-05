from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db.models import Aircraft

SKYBRARY_URL_TEMPLATE = "https://skybrary.aero/aircraft/{code}"

DISTANCE_PRESETS_KM = (100, 200, 300, 500)
PICKER_PAGE_SIZE = 8

_CHECK = "✅ "


def distance_presets_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for km in DISTANCE_PRESETS_KM:
        builder.button(text=f"{km} км", callback_data=f"af:dist:{km}")
    builder.adjust(4)
    return builder.as_markup()


def filters_main_keyboard(has_filters: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Высота", callback_data="af:menu:alt")
    builder.button(text="Тип", callback_data="af:menu:type")
    builder.button(text="Принадлежность", callback_data="af:menu:flag")
    builder.button(text="Показать список", callback_data="af:show")
    builder.button(text="Показать на карте", callback_data="af:draw")
    if has_filters:
        builder.button(text="Сбросить фильтры", callback_data="af:reset")
    builder.button(text="Готово", callback_data="af:done")
    builder.adjust(2)
    return builder.as_markup()


def filters_alt_keyboard(
    bands: list[tuple[int, int]], selected_index: int | None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, (band_min, band_max) in enumerate(bands):
        mark = _CHECK if index == selected_index else ""
        builder.button(
            text=f"{mark}{band_min}–{band_max} футов", callback_data=f"af:alt:band:{index}"
        )
    builder.button(text="Сбросить", callback_data="af:alt:clear")
    builder.button(text="Назад", callback_data="af:menu:main")
    builder.adjust(1)
    return builder.as_markup()


def filters_type_keyboard(options: list[str], selected: set[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for option in options:
        mark = _CHECK if option in selected else ""
        builder.button(text=f"{mark}{option}", callback_data=f"af:type:toggle:{option}")
    builder.button(text="Сбросить", callback_data="af:type:clear")
    builder.button(text="Назад", callback_data="af:menu:main")
    builder.adjust(2)
    return builder.as_markup()


def filters_flag_keyboard(options: list[str], selected: set[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for option in options:
        mark = _CHECK if option in selected else ""
        builder.button(text=f"{mark}{option}", callback_data=f"af:flag:toggle:{option}")
    builder.button(text="Сбросить", callback_data="af:flag:clear")
    builder.button(text="Назад", callback_data="af:menu:main")
    builder.adjust(2)
    return builder.as_markup()


def aircraft_picker_keyboard(aircraft: list[Aircraft], page: int) -> InlineKeyboardMarkup:
    start = page * PICKER_PAGE_SIZE
    page_items = aircraft[start : start + PICKER_PAGE_SIZE]

    builder = InlineKeyboardBuilder()
    for item in page_items:
        builder.button(
            text=item.reg_number or f"ID {item.id}", callback_data=f"pi:select:{item.id}"
        )
    builder.adjust(2)

    total_pages = -(-len(aircraft) // PICKER_PAGE_SIZE) or 1
    if total_pages > 1:
        nav_builder = InlineKeyboardBuilder()
        if page > 0:
            nav_builder.button(text="« Назад", callback_data=f"pi:page:{page - 1}")
        nav_builder.button(text=f"{page + 1}/{total_pages}", callback_data="pi:noop")
        if page < total_pages - 1:
            nav_builder.button(text="Вперёд »", callback_data=f"pi:page:{page + 1}")
        nav_builder.adjust(3)
        builder.attach(nav_builder)

    return builder.as_markup()


def skybrary_button(type_plane: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"О самолёте {type_plane} на SkyBrary",
        url=SKYBRARY_URL_TEMPLATE.format(code=type_plane),
    )
    return builder.as_markup()
