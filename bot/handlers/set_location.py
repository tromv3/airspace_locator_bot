from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories.history_repo import HistoryRepository
from bot.db.repositories.user_repo import UserRepository
from bot.keyboards.reply import address_keyboard, main_menu_keyboard
from bot.services.geocoder_client import DadataClient, GeocodingError
from bot.states.set_location import SetLocationStates

router = Router(name=__name__)

_COORDINATE_HINT = "Отправьте свои координаты в формате: \nширота, долгота (напр. 12.3456, 65.4321)"


@router.message(F.text == "Изменить местоположение")
async def request_location(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.set_state(SetLocationStates.location)
    await message.answer(
        "Отправьте точку на карте, либо выберите метод ввода:", reply_markup=address_keyboard()
    )
    await HistoryRepository(session).add(message.from_user.id, "Изменить местоположение")


@router.message(SetLocationStates.location, F.location)
async def set_location_from_point(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await _save_location(
        message, state, session, message.location.latitude, message.location.longitude
    )


@router.message(SetLocationStates.location, F.text == "Ввести адрес")
async def request_address(message: Message, state: FSMContext) -> None:
    await state.set_state(SetLocationStates.address)
    await message.answer(
        "Введите адрес:\n(напр. москва рабочая 36):", reply_markup=ReplyKeyboardRemove()
    )


@router.message(SetLocationStates.address, F.text)
async def set_location_from_address(
    message: Message, state: FSMContext, session: AsyncSession, dadata_client: DadataClient
) -> None:
    try:
        result = await dadata_client.geocode(message.text)
    except GeocodingError:
        result = None

    if result is None or result.lat is None or result.lon is None:
        await message.answer("К сожалению не удалось определить координаты. Попробуйте еще раз:")
        return

    await message.answer("Удалось определить следующие координаты:")
    await _save_location(
        message,
        state,
        session,
        result.lat,
        result.lon,
        extra=f"({result.result} | [{result.lat}, {result.lon}])",
    )


@router.message(SetLocationStates.location, F.text == "Ввести координаты")
async def request_coordinates(message: Message, state: FSMContext) -> None:
    await state.set_state(SetLocationStates.coordinate)
    await message.answer(_COORDINATE_HINT, reply_markup=ReplyKeyboardRemove())


@router.message(SetLocationStates.coordinate, F.text)
async def set_location_from_coordinates(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    parts = message.text.split(",")
    if len(parts) != 2 or not all(_is_number(part) for part in parts):
        await message.answer("Неверный ввод! Попробуйте еще раз.")
        return

    lat, lon = float(parts[0]), float(parts[1])
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        await message.answer("Неверный ввод! Попробуйте еще раз.")
        return

    await _save_location(message, state, session, lat, lon)


def _is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


async def _save_location(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    lat: float,
    lon: float,
    extra: str = "",
) -> None:
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    await repo.set_location(message.from_user.id, lat, lon)
    await state.clear()

    text = f"{user.name}, Ваше местоположение записано!"
    if extra:
        text += f"\n{extra}"
    await message.answer(text, reply_markup=main_menu_keyboard())
    await HistoryRepository(session).add(message.from_user.id, f"Новые координаты: {lat}, {lon}")
