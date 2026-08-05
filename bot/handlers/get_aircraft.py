from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.history_repo import HistoryRepository
from bot.db.repositories.user_repo import UserRepository
from bot.filters.is_digit import IsDigit
from bot.keyboards.inline import (
    distance_presets_keyboard,
    filters_alt_keyboard,
    filters_flag_keyboard,
    filters_main_keyboard,
    filters_type_keyboard,
)
from bot.keyboards.reply import main_menu_keyboard
from bot.services.airlabs_client import AirLabsClient, AirLabsError
from bot.services.geo_math import BBox, bbox_from_point
from bot.services.map_renderer import AircraftPoint, render_map
from bot.services.opensky_client import OpenSkyClient, OpenSkyError
from bot.states.get_aircraft import GetAircraftStates

router = Router(name=__name__)

_MIN_DISTANCE_KM = 100
_MAX_DISTANCE_KM = 500
_DISTANCE_HINT = "Необходимо ввести число от 100 до 500."
_ALT_BAND_COUNT = 4
_NO_MATCHES_HINT = "Нет воздушных судов, соответствующих фильтрам."
_NO_PRIOR_SEARCH_HINT = (
    'Еще не было ни одного поиска. Используйте "Получить данные о воздушных судах".'
)


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
        "Введите радиус поиска (от 100 до 500 км) или выберите вариант:",
        reply_markup=distance_presets_keyboard(),
    )
    await HistoryRepository(session).add(message.from_user.id, "Получить данные о воздушных судах")


@router.message(F.text == "Повторить последний поиск")
async def repeat_last_search(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    airlabs_client: AirLabsClient,
    opensky_client: OpenSkyClient,
) -> None:
    user = await UserRepository(session).get(message.from_user.id)
    if user.location_lat is None or user.location_lon is None:
        await message.answer(
            "Необходимо указать местоположение.", reply_markup=main_menu_keyboard()
        )
        return
    if user.last_distance_km is None:
        await message.answer(_NO_PRIOR_SEARCH_HINT, reply_markup=main_menu_keyboard())
        return

    await HistoryRepository(session).add(message.from_user.id, "Повторить последний поиск")
    await _fetch_and_show(
        message, state, session, airlabs_client, opensky_client, user.last_distance_km
    )


@router.message(GetAircraftStates.dist, IsDigit(True))
async def get_air(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    airlabs_client: AirLabsClient,
    opensky_client: OpenSkyClient,
) -> None:
    distance = int(message.text)
    if not (_MIN_DISTANCE_KM <= distance <= _MAX_DISTANCE_KM):
        await message.answer(_DISTANCE_HINT)
        return

    await _fetch_and_show(message, state, session, airlabs_client, opensky_client, distance)


@router.callback_query(GetAircraftStates.dist, F.data.startswith("af:dist:"))
async def get_air_preset(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    airlabs_client: AirLabsClient,
    opensky_client: OpenSkyClient,
) -> None:
    distance = int(callback.data.split(":")[2])
    await _fetch_and_show(callback, state, session, airlabs_client, opensky_client, distance)
    await callback.answer()


@router.message(GetAircraftStates.dist, IsDigit(False))
async def dist_incorrect(message: Message) -> None:
    await message.answer(_DISTANCE_HINT)


async def _fetch_and_show(
    target: Message | CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    airlabs_client: AirLabsClient,
    opensky_client: OpenSkyClient,
    distance: int,
) -> None:
    # `target` is duck-typed in tests (plain fakes, not real aiogram classes,
    # matching this codebase's handler-testing style) - distinguish by shape
    # rather than isinstance(target, CallbackQuery).
    is_callback = hasattr(target, "message")
    message = target.message if is_callback else target
    user_id = target.from_user.id

    user_repo = UserRepository(session)
    user = await user_repo.get(user_id)
    bbox = bbox_from_point(user.location_lat, user.location_lon, distance)

    note = ""
    try:
        aircraft = await airlabs_client.get_flights(bbox)
    except AirLabsError as error:
        logger.error(f"AirLabs request failed: {error}")
        try:
            aircraft = await opensky_client.get_flights(bbox)
            note = "\n(данные от OpenSky, тип судна может быть недоступен)"
        except OpenSkyError as fallback_error:
            logger.error(f"OpenSky fallback failed: {fallback_error}")
            text = "Не удалось получить данные о воздушных судах. Попробуйте позже."
            if is_callback:
                await message.edit_text(text)
            else:
                await message.answer(text)
            return

    await user_repo.set_search_area(user_id, bbox, distance)
    aircraft_repo = AircraftRepository(session)
    await aircraft_repo.replace_all(user_id, aircraft)
    count = await aircraft_repo.count_for_user(user_id)

    await state.set_state(GetAircraftStates.filters)
    await state.update_data(
        types=[], flags=[], alt_min=None, alt_max=None, alt_bands=None, alt_selected=None
    )

    text = f"Всего найдено {count} воздушных судов.{note}\nВыберите действие."
    if is_callback:
        await message.edit_text(text, reply_markup=filters_main_keyboard(has_filters=False))
    else:
        await message.answer(text, reply_markup=filters_main_keyboard(has_filters=False))
    await HistoryRepository(session).add(user_id, f"Всего найдено {count} воздушных судов")


def _has_filters(data: dict) -> bool:
    return bool(
        data.get("types") or data.get("flags") or data.get("alt_min") is not None
        or data.get("alt_max") is not None
    )


async def _compute_alt_bands(session: AsyncSession, user_id: int) -> list[list[int]]:
    aircraft = await AircraftRepository(session).list_for_user(user_id)
    altitudes = [item.alt for item in aircraft if item.alt is not None]
    if not altitudes:
        return [[0, 0]]

    alt_min, alt_max = min(altitudes), max(altitudes)
    if alt_min == alt_max:
        return [[alt_min, alt_max]]

    step = max(1, (alt_max - alt_min) // _ALT_BAND_COUNT)
    bands = []
    start = alt_min
    for i in range(_ALT_BAND_COUNT):
        end = alt_max if i == _ALT_BAND_COUNT - 1 else start + step
        bands.append([start, end])
        start = end
    return bands


@router.callback_query(GetAircraftStates.filters, F.data.startswith("af:menu:"))
async def filters_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    target = callback.data.split(":")[2]
    data = await state.get_data()
    user_id = callback.from_user.id

    if target == "alt":
        bands = data.get("alt_bands")
        if bands is None:
            bands = await _compute_alt_bands(session, user_id)
            await state.update_data(alt_bands=bands)
        await callback.message.edit_text(
            "Выберите диапазон высоты.",
            reply_markup=filters_alt_keyboard(bands, data.get("alt_selected")),
        )
    elif target == "type":
        options = sorted(await AircraftRepository(session).distinct_types(user_id))
        await callback.message.edit_text(
            "Выберите тип(ы).",
            reply_markup=filters_type_keyboard(options, set(data.get("types", []))),
        )
    elif target == "flag":
        raw_flags = await AircraftRepository(session).distinct_flags(user_id)
        options = sorted({flag.upper() for flag in raw_flags})
        await callback.message.edit_text(
            "Выберите принадлежность.",
            reply_markup=filters_flag_keyboard(options, set(data.get("flags", []))),
        )
    else:
        await callback.message.edit_text(
            "Выберите действие.", reply_markup=filters_main_keyboard(_has_filters(data))
        )
    await callback.answer()


@router.callback_query(GetAircraftStates.filters, F.data.startswith("af:alt:band:"))
async def filters_alt_select(callback: CallbackQuery, state: FSMContext) -> None:
    index = int(callback.data.split(":")[3])
    data = await state.get_data()
    bands = data.get("alt_bands") or []
    if index >= len(bands):
        await callback.answer()
        return

    if data.get("alt_selected") == index:
        await state.update_data(alt_min=None, alt_max=None, alt_selected=None)
    else:
        band_min, band_max = bands[index]
        await state.update_data(alt_min=band_min, alt_max=band_max, alt_selected=index)

    data = await state.get_data()
    await callback.message.edit_reply_markup(
        reply_markup=filters_alt_keyboard(bands, data.get("alt_selected"))
    )
    await callback.answer()


@router.callback_query(GetAircraftStates.filters, F.data == "af:alt:clear")
async def filters_alt_clear(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    bands = data.get("alt_bands") or []
    await state.update_data(alt_min=None, alt_max=None, alt_selected=None)
    await callback.message.edit_reply_markup(reply_markup=filters_alt_keyboard(bands, None))
    await callback.answer()


@router.callback_query(GetAircraftStates.filters, F.data.startswith("af:type:toggle:"))
async def filters_type_toggle(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    value = callback.data.split(":", 3)[3]
    data = await state.get_data()
    selected = set(data.get("types", []))
    if value in selected:
        selected.discard(value)
    else:
        selected.add(value)
    await state.update_data(types=sorted(selected))

    options = sorted(await AircraftRepository(session).distinct_types(callback.from_user.id))
    await callback.message.edit_reply_markup(
        reply_markup=filters_type_keyboard(options, selected)
    )
    await callback.answer()


@router.callback_query(GetAircraftStates.filters, F.data == "af:type:clear")
async def filters_type_clear(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await state.update_data(types=[])
    options = sorted(await AircraftRepository(session).distinct_types(callback.from_user.id))
    await callback.message.edit_reply_markup(reply_markup=filters_type_keyboard(options, set()))
    await callback.answer()


@router.callback_query(GetAircraftStates.filters, F.data.startswith("af:flag:toggle:"))
async def filters_flag_toggle(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    value = callback.data.split(":", 3)[3]
    data = await state.get_data()
    selected = set(data.get("flags", []))
    if value in selected:
        selected.discard(value)
    else:
        selected.add(value)
    await state.update_data(flags=sorted(selected))

    raw_flags = await AircraftRepository(session).distinct_flags(callback.from_user.id)
    options = sorted({flag.upper() for flag in raw_flags})
    await callback.message.edit_reply_markup(
        reply_markup=filters_flag_keyboard(options, selected)
    )
    await callback.answer()


@router.callback_query(GetAircraftStates.filters, F.data == "af:flag:clear")
async def filters_flag_clear(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await state.update_data(flags=[])
    raw_flags = await AircraftRepository(session).distinct_flags(callback.from_user.id)
    options = sorted({flag.upper() for flag in raw_flags})
    await callback.message.edit_reply_markup(reply_markup=filters_flag_keyboard(options, set()))
    await callback.answer()


@router.callback_query(GetAircraftStates.filters, F.data == "af:reset")
async def filters_reset(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(
        types=[], flags=[], alt_min=None, alt_max=None, alt_selected=None
    )
    await callback.message.edit_text(
        "Выберите действие.", reply_markup=filters_main_keyboard(has_filters=False)
    )
    await callback.answer("Фильтры сброшены")


@router.callback_query(GetAircraftStates.filters, F.data == "af:show")
async def filters_show(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    aircraft = await AircraftRepository(session).list_for_user(
        callback.from_user.id,
        alt_min=data.get("alt_min"),
        alt_max=data.get("alt_max"),
        types=data.get("types") or None,
        flags=data.get("flags") or None,
    )

    if not aircraft:
        await callback.message.answer(_NO_MATCHES_HINT)
        await callback.answer()
        return

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
            await callback.message.answer(chunk)
            chunk = ""
    if chunk:
        await callback.message.answer(chunk)

    await HistoryRepository(session).add(
        callback.from_user.id, f"Показано воздушных судов: {len(aircraft)}"
    )
    await callback.answer()


@router.callback_query(GetAircraftStates.filters, F.data == "af:draw")
async def filters_draw(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    user_id = callback.from_user.id
    aircraft = await AircraftRepository(session).list_for_user(
        user_id,
        alt_min=data.get("alt_min"),
        alt_max=data.get("alt_max"),
        types=data.get("types") or None,
        flags=data.get("flags") or None,
    )
    user = await UserRepository(session).get(user_id)

    if not aircraft or user.bbox_min_lat is None:
        await callback.message.answer(_NO_MATCHES_HINT)
        await callback.answer()
        return

    bbox = BBox(
        min_lat=user.bbox_min_lat,
        min_lon=user.bbox_min_lon,
        max_lat=user.bbox_max_lat,
        max_lon=user.bbox_max_lon,
    )
    points = [
        AircraftPoint(lat=item.latitude, lon=item.longitude, label=item.reg_number or "?")
        for item in aircraft
        if item.latitude is not None and item.longitude is not None
    ]

    try:
        png_bytes = await render_map(user.location_lat, user.location_lon, points, bbox)
    except Exception as error:
        logger.error(f"Map rendering failed: {error.__class__.__name__}: {error}")
        await callback.message.answer("Что-то пошло не так, попробуйте еще раз")
        await callback.answer()
        return

    await callback.message.answer_photo(BufferedInputFile(png_bytes, filename="map.png"))
    await HistoryRepository(session).add(user_id, "Показать на карте (отфильтровано)")
    await callback.answer()


@router.callback_query(GetAircraftStates.filters, F.data == "af:done")
async def filters_done(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Поиск завершён.")
    await callback.message.answer("Что дальше?", reply_markup=main_menu_keyboard())
    await callback.answer()
