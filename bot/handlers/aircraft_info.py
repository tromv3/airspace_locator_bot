from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.history_repo import HistoryRepository
from bot.keyboards.inline import plane_info_keyboard
from bot.keyboards.reply import main_menu_keyboard

router = Router(name=__name__)


@router.message(F.text == "Подробно о воздушном судне")
async def plane_info(message: Message, session: AsyncSession) -> None:
    plane_types = await AircraftRepository(session).distinct_types(message.from_user.id)
    if not plane_types:
        await message.answer(
            "Для начала необходимо получить данные!", reply_markup=main_menu_keyboard()
        )
    else:
        await message.answer(
            "При последнем поиске были следующие воздушные суда.",
            reply_markup=plane_info_keyboard(plane_types),
        )
        await message.answer("Что дальше?", reply_markup=main_menu_keyboard())

    await HistoryRepository(session).add(message.from_user.id, "Подробно о воздушном судне")
