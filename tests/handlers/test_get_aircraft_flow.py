import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.user_repo import UserRepository
from bot.handlers import get_aircraft
from bot.services.airlabs_client import AircraftInfo, AirLabsError
from bot.states.get_aircraft import GetAircraftStates

USER_ID = 1


class _FakeUser:
    def __init__(self, user_id):
        self.id = user_id


class _FakeMessage:
    def __init__(self, text=None, user_id=USER_ID):
        self.text = text
        self.from_user = _FakeUser(user_id)
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append(text)


class _FakeAirLabsClient:
    def __init__(self, aircraft=None, error=None):
        self._aircraft = aircraft or []
        self._error = error

    async def get_flights(self, bbox):
        if self._error:
            raise self._error
        return self._aircraft


@pytest.fixture
def state():
    storage = MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=USER_ID, user_id=USER_ID)
    return FSMContext(storage=storage, key=key)


async def _with_user_and_location(session) -> None:
    await UserRepository(session).get_or_create(USER_ID, "Ivan")
    await UserRepository(session).set_location(USER_ID, 55.75, 37.62)


async def _seed_aircraft(session) -> None:
    await AircraftRepository(session).replace_all(
        USER_ID,
        [
            AircraftInfo(
                reg_number="RA-1",
                flag="RU",
                type_plane="A320",
                latitude=1.0,
                longitude=2.0,
                alt=1000,
            ),
            AircraftInfo(
                reg_number="RA-2",
                flag="US",
                type_plane="B738",
                latitude=3.0,
                longitude=4.0,
                alt=5000,
            ),
        ],
    )


async def test_get_dist_requires_location(session, state):
    await UserRepository(session).get_or_create(USER_ID, "Ivan")
    message = _FakeMessage(text="Получить данные о воздушных судах")

    await get_aircraft.get_dist(message, state, session)

    assert await state.get_state() is None
    assert message.answers == ["Необходимо указать местоположение."]


async def test_get_dist_sets_state_when_location_known(session, state):
    await _with_user_and_location(session)
    message = _FakeMessage(text="Получить данные о воздушных судах")

    await get_aircraft.get_dist(message, state, session)

    assert await state.get_state() == GetAircraftStates.dist


async def test_get_air_rejects_out_of_range_distance(session, state):
    await _with_user_and_location(session)
    await state.set_state(GetAircraftStates.dist)
    message = _FakeMessage(text="50")

    await get_aircraft.get_air(message, state, session, _FakeAirLabsClient())

    assert message.answers == [get_aircraft._DISTANCE_HINT]
    assert await state.get_state() == GetAircraftStates.dist


async def test_get_air_fetches_and_stores_aircraft(session, state):
    await _with_user_and_location(session)
    await state.set_state(GetAircraftStates.dist)
    message = _FakeMessage(text="200")
    client = _FakeAirLabsClient(
        aircraft=[
            AircraftInfo(
                reg_number="RA-1",
                flag="RU",
                type_plane="A320",
                latitude=1.0,
                longitude=2.0,
                alt=1000,
            )
        ]
    )

    await get_aircraft.get_air(message, state, session, client)

    assert await state.get_state() == GetAircraftStates.filters
    count = await AircraftRepository(session).count_for_user(USER_ID)
    assert count == 1


async def test_get_air_reports_airlabs_failure(session, state):
    await _with_user_and_location(session)
    await state.set_state(GetAircraftStates.dist)
    message = _FakeMessage(text="200")
    client = _FakeAirLabsClient(error=AirLabsError("boom"))

    await get_aircraft.get_air(message, state, session, client)

    assert await state.get_state() == GetAircraftStates.dist
    assert "Не удалось получить данные" in message.answers[-1]


async def test_set_filter_alt_max_keeps_only_lower_aircraft(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filter_alt)
    await state.update_data(alt_filter="max")
    message = _FakeMessage(text="2000")

    await get_aircraft.set_filter_alt(message, state, session)

    remaining = await AircraftRepository(session).list_for_user(USER_ID)
    assert [a.reg_number for a in remaining] == ["RA-1"]
    assert await state.get_state() == GetAircraftStates.filters


async def test_filter_type_lists_and_applies(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    list_message = _FakeMessage(text="Фильтр по типу")

    await get_aircraft.filter_type(list_message, state, session)

    assert await state.get_state() == GetAircraftStates.filter_type
    data = await state.get_data()
    assert data["plane_types"] == ["A320", "B738"]

    choose_message = _FakeMessage(text="a320")
    await get_aircraft.set_filter_type(choose_message, state, session)

    remaining = await AircraftRepository(session).list_for_user(USER_ID)
    assert [a.reg_number for a in remaining] == ["RA-1"]
    assert await state.get_state() == GetAircraftStates.filters


async def test_set_filter_type_rejects_unknown_choice(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filter_type)
    await state.update_data(plane_types=["A320", "B738"])
    message = _FakeMessage(text="A319")

    await get_aircraft.set_filter_type(message, state, session)

    assert "Введите один из предложенных вариантов" in message.answers[-1]
    remaining = await AircraftRepository(session).list_for_user(USER_ID)
    assert len(remaining) == 2


async def test_filter_flag_lists_and_applies(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    list_message = _FakeMessage(text="Фильтр по принадлежности")

    await get_aircraft.filter_flag(list_message, state, session)

    data = await state.get_data()
    assert data["flags"] == ["RU", "US"]

    choose_message = _FakeMessage(text="ru")
    await get_aircraft.set_filter_flag(choose_message, state, session)

    remaining = await AircraftRepository(session).list_for_user(USER_ID)
    assert [a.reg_number for a in remaining] == ["RA-1"]
    assert await state.get_state() == GetAircraftStates.filters


async def test_show_lists_aircraft_and_clears_state(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    message = _FakeMessage(text="Показать воздушные суда")

    await get_aircraft.show(message, state, session)

    assert await state.get_state() is None
    assert any("Рег. номер: RA-1" in answer for answer in message.answers)
    assert message.answers[-1] == "Что дальше?"
