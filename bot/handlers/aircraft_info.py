from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Aircraft
from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.history_repo import HistoryRepository
from bot.keyboards.inline import aircraft_picker_keyboard, skybrary_button
from bot.keyboards.reply import main_menu_keyboard
from bot.services.planespotters_client import PlanespottersClient

router = Router(name=__name__)

_NO_DATA_HINT = "Для начала необходимо получить данные!"
_NOT_FOUND_HINT = "Судно не найдено."


@router.message(F.text == "Подробно о воздушном судне")
async def plane_info(message: Message, session: AsyncSession) -> None:
    aircraft = await AircraftRepository(session).list_for_user(message.from_user.id)
    if not aircraft:
        await message.answer(_NO_DATA_HINT, reply_markup=main_menu_keyboard())
    else:
        await message.answer(
            "Выберите воздушное судно.", reply_markup=aircraft_picker_keyboard(aircraft, page=0)
        )

    await HistoryRepository(session).add(message.from_user.id, "Подробно о воздушном судне")


@router.callback_query(F.data.startswith("pi:page:"))
async def plane_info_page(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split(":")[2])
    aircraft = await AircraftRepository(session).list_for_user(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=aircraft_picker_keyboard(aircraft, page))
    await callback.answer()


@router.callback_query(F.data == "pi:noop")
async def plane_info_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("pi:select:"))
async def plane_info_select(
    callback: CallbackQuery, session: AsyncSession, planespotters_client: PlanespottersClient
) -> None:
    aircraft_id = int(callback.data.split(":")[2])
    item = await AircraftRepository(session).get_by_id(aircraft_id)
    if item is None or item.user_id != callback.from_user.id:
        await callback.answer(_NOT_FOUND_HINT, show_alert=True)
        return

    caption = _format_aircraft(item)
    keyboard = skybrary_button(item.type_plane) if item.type_plane else None

    photo_url = None
    if item.reg_number:
        photo_url = await planespotters_client.get_photo_url(item.reg_number)

    if photo_url:
        await callback.message.answer_photo(photo_url, caption=caption, reply_markup=keyboard)
    else:
        await callback.message.answer(caption, reply_markup=keyboard)

    await callback.answer()


def _format_aircraft(item: Aircraft) -> str:
    lines = []
    if item.reg_number is not None:
        lines.append(f"Рег. номер: {item.reg_number}")
    if item.flag is not None:
        lines.append(f"Страна: {item.flag}")
    if item.type_plane is not None:
        lines.append(f"Тип: {item.type_plane}")
    if item.latitude is not None and item.longitude is not None:
        lines.append(f"Широта: {item.latitude} | Долгота: {item.longitude}")
    if item.alt is not None:
        lines.append(f"Высота: {item.alt}")
    lines.append(f"Источник: {item.source}")
    return "\n".join(lines)
