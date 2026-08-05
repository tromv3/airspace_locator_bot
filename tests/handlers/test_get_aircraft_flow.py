import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.user_repo import UserRepository
from bot.handlers import get_aircraft
from bot.services.airlabs_client import AirLabsError
from bot.services.flight_types import AircraftInfo
from bot.services.opensky_client import OpenSkyError
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
        self.edits = []
        self.markup_edits = []
        self.photos = []

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))

    async def edit_text(self, text, reply_markup=None):
        self.edits.append((text, reply_markup))

    async def edit_reply_markup(self, reply_markup=None):
        self.markup_edits.append(reply_markup)

    async def answer_photo(self, photo, reply_markup=None):
        self.photos.append(photo)


class _FakeCallbackQuery:
    def __init__(self, data, message, user_id=USER_ID):
        self.data = data
        self.message = message
        self.from_user = _FakeUser(user_id)
        self.answered = []

    async def answer(self, text=None, show_alert=False):
        self.answered.append(text)


class _FakeAirLabsClient:
    def __init__(self, aircraft=None, error=None):
        self._aircraft = aircraft or []
        self._error = error

    async def get_flights(self, bbox):
        if self._error:
            raise self._error
        return self._aircraft


class _FakeOpenSkyClient:
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


def _one_aircraft(source="airlabs", **overrides) -> list[AircraftInfo]:
    fields = {
        "reg_number": "RA-1",
        "flag": "RU",
        "type_plane": "A320",
        "latitude": 1.0,
        "longitude": 2.0,
        "alt": 1000,
        "source": source,
    }
    fields.update(overrides)
    return [AircraftInfo(**fields)]


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
                source="airlabs",
            ),
            AircraftInfo(
                reg_number="RA-2",
                flag="US",
                type_plane="B738",
                latitude=3.0,
                longitude=4.0,
                alt=5000,
                source="airlabs",
            ),
        ],
    )


async def test_get_dist_requires_location(session, state):
    await UserRepository(session).get_or_create(USER_ID, "Ivan")
    message = _FakeMessage(text="Получить данные о воздушных судах")

    await get_aircraft.get_dist(message, state, session)

    assert await state.get_state() is None
    assert message.answers[0][0] == "Необходимо указать местоположение."


async def test_get_dist_sets_state_and_shows_presets(session, state):
    await _with_user_and_location(session)
    message = _FakeMessage(text="Получить данные о воздушных судах")

    await get_aircraft.get_dist(message, state, session)

    assert await state.get_state() == GetAircraftStates.dist
    assert message.answers[0][1] is not None


async def test_get_air_rejects_out_of_range_distance(session, state):
    await _with_user_and_location(session)
    await state.set_state(GetAircraftStates.dist)
    message = _FakeMessage(text="50")

    await get_aircraft.get_air(
        message, state, session, _FakeAirLabsClient(), _FakeOpenSkyClient()
    )

    assert message.answers[0][0] == get_aircraft._DISTANCE_HINT
    assert await state.get_state() == GetAircraftStates.dist


async def test_get_air_fetches_and_stores_aircraft(session, state):
    await _with_user_and_location(session)
    await state.set_state(GetAircraftStates.dist)
    message = _FakeMessage(text="200")
    client = _FakeAirLabsClient(aircraft=_one_aircraft())

    await get_aircraft.get_air(message, state, session, client, _FakeOpenSkyClient())

    assert await state.get_state() == GetAircraftStates.filters
    count = await AircraftRepository(session).count_for_user(USER_ID)
    assert count == 1
    user = await UserRepository(session).get(USER_ID)
    assert user.last_distance_km == 200


async def test_get_air_falls_back_to_opensky_on_airlabs_error(session, state):
    await _with_user_and_location(session)
    await state.set_state(GetAircraftStates.dist)
    message = _FakeMessage(text="200")
    airlabs_client = _FakeAirLabsClient(error=AirLabsError("boom"))
    opensky_client = _FakeOpenSkyClient(aircraft=_one_aircraft(source="opensky"))

    await get_aircraft.get_air(message, state, session, airlabs_client, opensky_client)

    assert await state.get_state() == GetAircraftStates.filters
    stored = await AircraftRepository(session).list_for_user(USER_ID)
    assert stored[0].source == "opensky"
    assert "OpenSky" in message.answers[-1][0]


async def test_get_air_reports_failure_when_both_sources_fail(session, state):
    await _with_user_and_location(session)
    await state.set_state(GetAircraftStates.dist)
    message = _FakeMessage(text="200")
    airlabs_client = _FakeAirLabsClient(error=AirLabsError("boom"))
    opensky_client = _FakeOpenSkyClient(error=OpenSkyError("boom too"))

    await get_aircraft.get_air(message, state, session, airlabs_client, opensky_client)

    assert await state.get_state() == GetAircraftStates.dist
    assert "Не удалось получить данные" in message.answers[-1][0]


async def test_get_air_preset_fetches_via_callback_and_edits_message(session, state):
    await _with_user_and_location(session)
    await state.set_state(GetAircraftStates.dist)
    prompt_message = _FakeMessage()
    callback = _FakeCallbackQuery("af:dist:200", prompt_message)
    client = _FakeAirLabsClient(aircraft=_one_aircraft())

    await get_aircraft.get_air_preset(callback, state, session, client, _FakeOpenSkyClient())

    assert await state.get_state() == GetAircraftStates.filters
    assert prompt_message.edits
    assert callback.answered


async def test_repeat_last_search_requires_location(session, state):
    await UserRepository(session).get_or_create(USER_ID, "Ivan")
    message = _FakeMessage(text="Повторить последний поиск")

    await get_aircraft.repeat_last_search(
        message, state, session, _FakeAirLabsClient(), _FakeOpenSkyClient()
    )

    assert message.answers[0][0] == "Необходимо указать местоположение."


async def test_repeat_last_search_requires_prior_search(session, state):
    await _with_user_and_location(session)
    message = _FakeMessage(text="Повторить последний поиск")

    await get_aircraft.repeat_last_search(
        message, state, session, _FakeAirLabsClient(), _FakeOpenSkyClient()
    )

    assert message.answers[0][0] == get_aircraft._NO_PRIOR_SEARCH_HINT


async def test_repeat_last_search_reuses_saved_distance(session, state):
    await _with_user_and_location(session)
    user_repo = UserRepository(session)
    bbox = get_aircraft.bbox_from_point(55.75, 37.62, 200)
    await user_repo.set_search_area(USER_ID, bbox, 200)
    message = _FakeMessage(text="Повторить последний поиск")
    client = _FakeAirLabsClient(aircraft=_one_aircraft())

    await get_aircraft.repeat_last_search(message, state, session, client, _FakeOpenSkyClient())

    assert await state.get_state() == GetAircraftStates.filters
    assert await AircraftRepository(session).count_for_user(USER_ID) == 1


async def test_filters_menu_alt_computes_bands_once(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    message = _FakeMessage()
    callback = _FakeCallbackQuery("af:menu:alt", message)

    await get_aircraft.filters_menu(callback, state, session)

    data = await state.get_data()
    assert data["alt_bands"] == [[1000, 2000], [2000, 3000], [3000, 4000], [4000, 5000]]


async def test_filters_alt_select_toggle_sets_and_clears_range(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    await state.update_data(alt_bands=[[1000, 2000], [2000, 3000], [3000, 4000], [4000, 5000]])
    message = _FakeMessage()
    select = _FakeCallbackQuery("af:alt:band:3", message)

    await get_aircraft.filters_alt_select(select, state)

    data = await state.get_data()
    assert (data["alt_min"], data["alt_max"], data["alt_selected"]) == (4000, 5000, 3)

    deselect = _FakeCallbackQuery("af:alt:band:3", message)
    await get_aircraft.filters_alt_select(deselect, state)

    data = await state.get_data()
    assert (data["alt_min"], data["alt_max"], data["alt_selected"]) == (None, None, None)


async def test_filters_type_toggle_adds_and_removes(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    message = _FakeMessage()

    toggle_on = _FakeCallbackQuery("af:type:toggle:A320", message)
    await get_aircraft.filters_type_toggle(toggle_on, state, session)
    assert (await state.get_data())["types"] == ["A320"]

    toggle_off = _FakeCallbackQuery("af:type:toggle:A320", message)
    await get_aircraft.filters_type_toggle(toggle_off, state, session)
    assert (await state.get_data())["types"] == []


async def test_filters_flag_clear_resets_selection(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    await state.update_data(flags=["RU"])
    message = _FakeMessage()
    callback = _FakeCallbackQuery("af:flag:clear", message)

    await get_aircraft.filters_flag_clear(callback, state, session)

    assert (await state.get_data())["flags"] == []


async def test_filters_reset_clears_all_criteria(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    await state.update_data(types=["A320"], flags=["RU"], alt_min=1000, alt_max=2000)
    message = _FakeMessage()
    callback = _FakeCallbackQuery("af:reset", message)

    await get_aircraft.filters_reset(callback, state)

    data = await state.get_data()
    assert data["types"] == []
    assert data["flags"] == []
    assert data["alt_min"] is None
    assert data["alt_max"] is None


async def test_filters_show_lists_matching_aircraft(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    await state.update_data(types=[], flags=[], alt_min=None, alt_max=None)
    message = _FakeMessage()
    callback = _FakeCallbackQuery("af:show", message)

    await get_aircraft.filters_show(callback, state, session)

    assert any("RA-1" in text for text, _ in message.answers)
    assert any("RA-2" in text for text, _ in message.answers)


async def test_filters_show_reports_no_matches(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    await state.update_data(types=["B777"], flags=[], alt_min=None, alt_max=None)
    message = _FakeMessage()
    callback = _FakeCallbackQuery("af:show", message)

    await get_aircraft.filters_show(callback, state, session)

    assert message.answers == [(get_aircraft._NO_MATCHES_HINT, None)]


async def test_filters_draw_renders_filtered_map(session, state, monkeypatch):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    bbox = get_aircraft.bbox_from_point(55.75, 37.62, 200)
    await UserRepository(session).set_search_area(USER_ID, bbox, 200)
    await state.set_state(GetAircraftStates.filters)
    await state.update_data(types=["A320"], flags=[], alt_min=None, alt_max=None)
    message = _FakeMessage()
    callback = _FakeCallbackQuery("af:draw", message)

    async def fake_render_map(user_lat, user_lon, aircraft, bbox):
        assert aircraft == [get_aircraft.AircraftPoint(lat=1.0, lon=2.0, label="1")]
        return b"\x89PNGfakebytes"

    monkeypatch.setattr(get_aircraft, "render_map", fake_render_map)

    await get_aircraft.filters_draw(callback, state, session)

    assert len(message.photos) == 1


async def test_filters_done_clears_state_and_shows_main_menu(session, state):
    await _with_user_and_location(session)
    await _seed_aircraft(session)
    await state.set_state(GetAircraftStates.filters)
    message = _FakeMessage()
    callback = _FakeCallbackQuery("af:done", message)

    await get_aircraft.filters_done(callback, state)

    assert await state.get_state() is None
    assert message.answers[-1][1] is not None
