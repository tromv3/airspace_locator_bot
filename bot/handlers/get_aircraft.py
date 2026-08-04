from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.history_repo import HistoryRepository
from bot.db.repositories.user_repo import UserRepository
from bot.filters.is_digit import IsDigit
from bot.keyboards.reply import filters_keyboard, main_menu_keyboard
from bot.services.airlabs_client import AirLabsClient, AirLabsError
from bot.services.geo_math import bbox_from_point
from bot.states.get_aircraft import GetAircraftStates

router = Router(name=__name__)

_MIN_DISTANCE_KM = 100
_MAX_DISTANCE_KM = 500
_DISTANCE_HINT = "Необходимо ввести число от 100 до 500."


@router.message(F.text == "Получить данные о воздушных судах")
async def get_dist(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await UserRepository(session).get(message.from_user.id)
    if user.location_lat is None or user.location_lon is None:
        await message.answer(
            "Необходимо указать местоположение.", reply_markup=main_menu_keyboard()
        )
        return

    await state.set_state(GetAircraftStates.dist)
    await message.answer(
        "Введите радиус поиска (от 100 до 500 км):", reply_markup=ReplyKeyboardRemove()
    )
    await HistoryRepository(session).add(message.from_user.id, "Получить данные о воздушных судах")


@router.message(GetAircraftStates.dist, IsDigit(True))
async def get_air(
    message: Message, state: FSMContext, session: AsyncSession, airlabs_client: AirLabsClient
) -> None:
    distance = int(message.text)
    if not (_MIN_DISTANCE_KM <= distance <= _MAX_DISTANCE_KM):
        await message.answer(_DISTANCE_HINT)
        return

    user_repo = UserRepository(session)
    user = await user_repo.get(message.from_user.id)
    bbox = bbox_from_point(user.location_lat, user.location_lon, distance)

    try:
        aircraft = await airlabs_client.get_flights(bbox)
    except AirLabsError as error:
        logger.error(f"AirLabs request failed: {error}")
        await message.answer("Не удалось получить данные о воздушных судах. Попробуйте позже.")
        return

    await user_repo.set_search_area(message.from_user.id, bbox)
    aircraft_repo = AircraftRepository(session)
    await aircraft_repo.replace_all(message.from_user.id, aircraft)
    count = await aircraft_repo.count_for_user(message.from_user.id)

    await state.set_state(GetAircraftStates.filters)
    await message.answer(
        f"Всего найдено {count} воздушных судов. Выберите действие.",
        reply_markup=filters_keyboard(),
    )
    await HistoryRepository(session).add(
        message.from_user.id, f"Всего найдено {count} воздушных судов"
    )


@router.message(GetAircraftStates.dist, IsDigit(False))
async def dist_incorrect(message: Message) -> None:
    await message.answer(_DISTANCE_HINT)


@router.message(GetAircraftStates.filters, F.text == "Фильтр по высоте (max)")
async def filter_alt_max(message: Message, state: FSMContext) -> None:
    await state.set_state(GetAircraftStates.filter_alt)
    await state.update_data(alt_filter="max")
    await message.answer("Введите максимальную высоту.", reply_markup=ReplyKeyboardRemove())


@router.message(GetAircraftStates.filters, F.text == "Фильтр по высоте (min)")
async def filter_alt_min(message: Message, state: FSMContext) -> None:
    await state.set_state(GetAircraftStates.filter_alt)
    await state.update_data(alt_filter="min")
    await message.answer("Введите минимальную высоту.", reply_markup=ReplyKeyboardRemove())


@router.message(GetAircraftStates.filter_alt, IsDigit(True))
async def set_filter_alt(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    value = int(message.text)
    aircraft_repo = AircraftRepository(session)
    if data.get("alt_filter") == "max":
        await aircraft_repo.delete_where_alt_gte(message.from_user.id, value)
    else:
        await aircraft_repo.delete_where_alt_lte(message.from_user.id, value)

    count = await aircraft_repo.count_for_user(message.from_user.id)
    await state.set_state(GetAircraftStates.filters)
    await message.answer(
        f"Фильтр применен.\nВсего воздушных судов: {count}.\nВыберите действие:",
        reply_markup=filters_keyboard(),
    )
    await HistoryRepository(session).add(message.from_user.id, "Применен фильтр по высоте.")


@router.message(GetAircraftStates.filter_alt, IsDigit(False))
async def alt_incorrect(message: Message) -> None:
    await message.answer("Необходимо ввести положительное число.")


@router.message(GetAircraftStates.filters, F.text == "Фильтр по типу")
async def filter_type(message: Message, state: FSMContext, session: AsyncSession) -> None:
    plane_types = sorted(await AircraftRepository(session).distinct_types(message.from_user.id))
    await state.set_state(GetAircraftStates.filter_type)
    await state.update_data(plane_types=plane_types)
    await message.answer(
        f"Введите тип:\n{', '.join(plane_types)}", reply_markup=ReplyKeyboardRemove()
    )


@router.message(GetAircraftStates.filter_type)
async def set_filter_type(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    plane_types = data.get("plane_types", [])
    choice = (message.text or "").upper()
    if choice not in plane_types:
        await message.answer(f"Введите один из предложенных вариантов:\n{', '.join(plane_types)}")
        return

    aircraft_repo = AircraftRepository(session)
    await aircraft_repo.delete_where_type_not(message.from_user.id, choice)
    count = await aircraft_repo.count_for_user(message.from_user.id)
    await state.set_state(GetAircraftStates.filters)
    await message.answer(
        f"Фильтр применен.\nВсего воздушных судов: {count}.\nВыберите действие:",
        reply_markup=filters_keyboard(),
    )
    await HistoryRepository(session).add(message.from_user.id, "Применен фильтр по типу судна.")


@router.message(GetAircraftStates.filters, F.text == "Фильтр по принадлежности")
async def filter_flag(message: Message, state: FSMContext, session: AsyncSession) -> None:
    raw_flags = await AircraftRepository(session).distinct_flags(message.from_user.id)
    flags = sorted({flag.upper() for flag in raw_flags})
    await state.set_state(GetAircraftStates.filter_flag)
    await state.update_data(flags=flags)
    await message.answer(
        f"Введите принадлежность:\n{', '.join(flags)}", reply_markup=ReplyKeyboardRemove()
    )


@router.message(GetAircraftStates.filter_flag)
async def set_filter_flag(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    flags = data.get("flags", [])
    choice = (message.text or "").upper()
    if choice not in flags:
        await message.answer(f"Введите один из предложенных вариантов:\n{', '.join(flags)}")
        return

    aircraft_repo = AircraftRepository(session)
    await aircraft_repo.delete_where_flag_not(message.from_user.id, choice)
    count = await aircraft_repo.count_for_user(message.from_user.id)
    await state.set_state(GetAircraftStates.filters)
    await message.answer(
        f"Фильтр применен.\nВсего воздушных судов: {count}.\nВыберите действие:",
        reply_markup=filters_keyboard(),
    )
    await HistoryRepository(session).add(
        message.from_user.id, "Применен фильтр по принадлежности судна."
    )


@router.message(GetAircraftStates.filters, F.text == "Показать воздушные суда")
async def show(message: Message, state: FSMContext, session: AsyncSession) -> None:
    aircraft = await AircraftRepository(session).list_for_user(message.from_user.id)

    chunk = ""
    for item in aircraft:
        if item.reg_number is not None:
            chunk += f"Рег. номер: {item.reg_number}\n"
        if item.flag is not None:
            chunk += f"Страна: {item.flag}\n"
        if item.type_plane is not None:
            chunk += f"Тип: {item.type_plane}\n"
        if item.latitude is not None and item.longitude is not None:
            chunk += f"Широта: {item.latitude} | Долгота: {item.longitude}\n"
        if item.alt is not None:
            chunk += f"Высота: {item.alt}\n"
        chunk += "-" * 10 + "\n"
        if len(chunk) + 100 > 4000:
            await message.answer(chunk)
            chunk = ""
    if chunk:
        await message.answer(chunk)

    await state.clear()
    await message.answer("Что дальше?", reply_markup=main_menu_keyboard())
    await HistoryRepository(session).add(
        message.from_user.id, f"Показано воздушных судов: {len(aircraft)}"
    )
