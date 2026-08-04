import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.db.repositories.user_repo import UserRepository
from bot.handlers import set_location
from bot.services.geocoder_client import GeocodeResult, GeocodingError
from bot.states.set_location import SetLocationStates

USER_ID = 1


class _FakeUser:
    def __init__(self, user_id):
        self.id = user_id


class _FakeLocation:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude


class _FakeMessage:
    def __init__(self, text=None, location=None, user_id=USER_ID):
        self.text = text
        self.location = location
        self.from_user = _FakeUser(user_id)
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append(text)


class _FakeDadataClient:
    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error

    async def geocode(self, address):
        if self._error:
            raise self._error
        return self._result


@pytest.fixture
def state():
    storage = MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=USER_ID, user_id=USER_ID)
    return FSMContext(storage=storage, key=key)


async def _with_user(session) -> None:
    await UserRepository(session).get_or_create(USER_ID, "Ivan")


async def test_request_location_sets_state_and_logs_history(session, state):
    await _with_user(session)
    message = _FakeMessage(text="Изменить местоположение")

    await set_location.request_location(message, state, session)

    assert await state.get_state() == SetLocationStates.location
    assert message.answers


async def test_set_location_from_point_saves_and_clears_state(session, state):
    await _with_user(session)
    await state.set_state(SetLocationStates.location)
    message = _FakeMessage(location=_FakeLocation(55.75, 37.62))

    await set_location.set_location_from_point(message, state, session)

    user = await UserRepository(session).get(USER_ID)
    assert (user.location_lat, user.location_lon) == (55.75, 37.62)
    assert await state.get_state() is None


async def test_set_location_from_coordinates_rejects_out_of_range(session, state):
    await _with_user(session)
    await state.set_state(SetLocationStates.coordinate)
    message = _FakeMessage(text="200, 37.62")

    await set_location.set_location_from_coordinates(message, state, session)

    user = await UserRepository(session).get(USER_ID)
    assert user.location_lat is None
    assert message.answers == ["Неверный ввод! Попробуйте еще раз."]


async def test_set_location_from_coordinates_rejects_non_numeric(session, state):
    await _with_user(session)
    await state.set_state(SetLocationStates.coordinate)
    message = _FakeMessage(text="north, east")

    await set_location.set_location_from_coordinates(message, state, session)

    assert message.answers == ["Неверный ввод! Попробуйте еще раз."]


async def test_set_location_from_coordinates_accepts_valid_input(session, state):
    await _with_user(session)
    await state.set_state(SetLocationStates.coordinate)
    message = _FakeMessage(text="55.75, 37.62")

    await set_location.set_location_from_coordinates(message, state, session)

    user = await UserRepository(session).get(USER_ID)
    assert (user.location_lat, user.location_lon) == (55.75, 37.62)
    assert await state.get_state() is None


async def test_set_location_from_address_saves_on_success(session, state):
    await _with_user(session)
    await state.set_state(SetLocationStates.address)
    message = _FakeMessage(text="москва рабочая 36")
    dadata_client = _FakeDadataClient(result=GeocodeResult(lat=55.75, lon=37.62, result="Москва"))

    await set_location.set_location_from_address(message, state, session, dadata_client)

    user = await UserRepository(session).get(USER_ID)
    assert (user.location_lat, user.location_lon) == (55.75, 37.62)
    assert await state.get_state() is None


async def test_set_location_from_address_reports_failure(session, state):
    await _with_user(session)
    await state.set_state(SetLocationStates.address)
    message = _FakeMessage(text="???")
    dadata_client = _FakeDadataClient(error=GeocodingError("boom"))

    await set_location.set_location_from_address(message, state, session, dadata_client)

    user = await UserRepository(session).get(USER_ID)
    assert user.location_lat is None
    assert "не удалось определить координаты" in message.answers[-1]
    assert await state.get_state() == SetLocationStates.address
