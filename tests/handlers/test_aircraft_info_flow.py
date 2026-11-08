from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.user_repo import UserRepository
from bot.handlers import aircraft_info
from bot.services.flight_types import AircraftInfo

USER_ID = 1


class _FakeUser:
    def __init__(self, user_id):
        self.id = user_id


class _FakeMessage:
    def __init__(self, user_id=USER_ID):
        self.from_user = _FakeUser(user_id)
        self.answers = []
        self.photos = []
        self.markup_edits = []

    async def answer(self, text, reply_markup=None):
        self.answers.append((text, reply_markup))

    async def answer_photo(self, photo, caption=None, reply_markup=None):
        self.photos.append((photo, caption, reply_markup))

    async def edit_reply_markup(self, reply_markup=None):
        self.markup_edits.append(reply_markup)


class _FakeCallbackQuery:
    def __init__(self, data, message, user_id=USER_ID):
        self.data = data
        self.message = message
        self.from_user = _FakeUser(user_id)
        self.answered = []

    async def answer(self, text=None, show_alert=False):
        self.answered.append((text, show_alert))


class _FakePlanespottersClient:
    def __init__(self, url=None):
        self._url = url

    async def get_photo_url(self, reg_number):
        return self._url


async def _seed_two_aircraft(session) -> None:
    await UserRepository(session).get_or_create(USER_ID, "Ivan")
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
                source="opensky",
            ),
        ],
    )


async def test_plane_info_requires_data_when_no_aircraft(session):
    await UserRepository(session).get_or_create(USER_ID, "Ivan")
    message = _FakeMessage()

    await aircraft_info.plane_info(message, session)

    assert message.answers[0][0] == aircraft_info._NO_DATA_HINT


async def test_plane_info_shows_picker_keyboard(session):
    await _seed_two_aircraft(session)
    message = _FakeMessage()

    await aircraft_info.plane_info(message, session)

    assert message.answers[0][0] == "Выберите воздушное судно."
    buttons = [button for row in message.answers[0][1].inline_keyboard for button in row]
    labels = {button.text for button in buttons}
    assert labels == {"RA-1", "RA-2"}


async def test_plane_info_select_sends_text_when_no_photo(session):
    await _seed_two_aircraft(session)
    aircraft = await AircraftRepository(session).list_for_user(USER_ID)
    target = next(a for a in aircraft if a.reg_number == "RA-1")
    message = _FakeMessage()
    callback = _FakeCallbackQuery(f"pi:select:{target.id}", message)

    await aircraft_info.plane_info_select(callback, session, _FakePlanespottersClient(url=None))

    assert message.photos == []
    text, keyboard = message.answers[0]
    assert "RA-1" in text
    assert "Источник: airlabs" in text
    assert keyboard is not None


async def test_plane_info_select_sends_photo_when_available(session):
    await _seed_two_aircraft(session)
    aircraft = await AircraftRepository(session).list_for_user(USER_ID)
    target = next(a for a in aircraft if a.reg_number == "RA-2")
    message = _FakeMessage()
    callback = _FakeCallbackQuery(f"pi:select:{target.id}", message)

    await aircraft_info.plane_info_select(
        callback, session, _FakePlanespottersClient(url="https://example.com/photo.jpg")
    )

    assert message.answers == []
    photo, caption, keyboard = message.photos[0]
    assert photo == "https://example.com/photo.jpg"
    assert "RA-2" in caption


async def test_plane_info_select_rejects_unknown_id(session):
    await _seed_two_aircraft(session)
    message = _FakeMessage()
    callback = _FakeCallbackQuery("pi:select:99999", message)

    await aircraft_info.plane_info_select(callback, session, _FakePlanespottersClient())

    assert callback.answered == [(aircraft_info._NOT_FOUND_HINT, True)]
    assert message.answers == []
    assert message.photos == []


async def test_plane_info_page_switches_page(session):
    await UserRepository(session).get_or_create(USER_ID, "Ivan")
    await AircraftRepository(session).replace_all(
        USER_ID,
        [
            AircraftInfo(
                reg_number=f"RA-{i}",
                flag="RU",
                type_plane="A320",
                latitude=1.0,
                longitude=2.0,
                alt=1000,
                source="airlabs",
            )
            for i in range(10)
        ],
    )
    message = _FakeMessage()
    callback = _FakeCallbackQuery("pi:page:1", message)

    await aircraft_info.plane_info_page(callback, session)

    assert len(message.markup_edits) == 1
