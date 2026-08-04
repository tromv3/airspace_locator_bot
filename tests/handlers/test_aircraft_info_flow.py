from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.user_repo import UserRepository
from bot.handlers import aircraft_info
from bot.services.airlabs_client import AircraftInfo

USER_ID = 1


class _FakeUser:
    def __init__(self, user_id):
        self.id = user_id


class _FakeMessage:
    def __init__(self, user_id=USER_ID):
        self.from_user = _FakeUser(user_id)
        self.answers = []
        self.keyboards = []

    async def answer(self, text, reply_markup=None):
        self.answers.append(text)
        self.keyboards.append(reply_markup)


async def test_plane_info_requires_data_when_no_aircraft(session):
    await UserRepository(session).get_or_create(USER_ID, "Ivan")
    message = _FakeMessage()

    await aircraft_info.plane_info(message, session)

    assert message.answers == ["Для начала необходимо получить данные!"]


async def test_plane_info_shows_inline_keyboard_for_known_types(session):
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
            ),
            AircraftInfo(
                reg_number="RA-2",
                flag="US",
                type_plane="b738",
                latitude=3.0,
                longitude=4.0,
                alt=5000,
            ),
        ],
    )
    message = _FakeMessage()

    await aircraft_info.plane_info(message, session)

    assert message.answers[0] == "При последнем поиске были следующие воздушные суда."
    buttons = [
        button
        for row in message.keyboards[0].inline_keyboard
        for button in row
    ]
    urls = {button.url for button in buttons}
    assert urls == {
        "https://skybrary.aero/aircraft/A320",
        "https://skybrary.aero/aircraft/B738",
    }
    assert message.answers[1] == "Что дальше?"
