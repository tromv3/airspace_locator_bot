from aiogram import F, Router
from aiogram.types import BufferedInputFile, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.history_repo import HistoryRepository
from bot.db.repositories.user_repo import UserRepository
from bot.keyboards.reply import main_menu_keyboard
from bot.services.geo_math import BBox
from bot.services.map_renderer import render_map

router = Router(name=__name__)

_NO_DATA_HINT = "Для начала необходимо получить данные!"


@router.message(F.text == "Отрисовать полученные данные")
async def draw(message: Message, session: AsyncSession) -> None:
    aircraft = await AircraftRepository(session).list_for_user(message.from_user.id)
    user = await UserRepository(session).get(message.from_user.id)

    if not aircraft or user.bbox_min_lat is None:
        await message.answer(_NO_DATA_HINT, reply_markup=main_menu_keyboard())
        return

    bbox = BBox(
        min_lat=user.bbox_min_lat,
        min_lon=user.bbox_min_lon,
        max_lat=user.bbox_max_lat,
        max_lon=user.bbox_max_lon,
    )
    points = [
        (item.latitude, item.longitude)
        for item in aircraft
        if item.latitude is not None and item.longitude is not None
    ]

    try:
        png_bytes = await render_map(user.location_lat, user.location_lon, points, bbox)
    except Exception as error:
        logger.error(f"Map rendering failed: {error.__class__.__name__}: {error}")
        await message.answer(
            "Что-то пошло не так, попробуйте еще раз", reply_markup=main_menu_keyboard()
        )
        return

    await message.answer_photo(BufferedInputFile(png_bytes, filename="map.png"))
    await message.answer(f"{user.name}, что дальше?", reply_markup=main_menu_keyboard())
    await HistoryRepository(session).add(message.from_user.id, "Отрисовать полученные данные")
