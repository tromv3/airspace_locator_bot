from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.user_repo import UserRepository
from bot.handlers import draw
from bot.services.airlabs_client import AircraftInfo
from bot.services.geo_math import BBox

USER_ID = 1


class _FakeUser:
    def __init__(self, user_id):
        self.id = user_id


class _FakeMessage:
    def __init__(self, user_id=USER_ID):
        self.from_user = _FakeUser(user_id)
        self.answers = []
        self.photos = []

    async def answer(self, text, reply_markup=None):
        self.answers.append(text)

    async def answer_photo(self, photo, reply_markup=None):
        self.photos.append(photo)


def _one_aircraft() -> list[AircraftInfo]:
    return [
        AircraftInfo(
            reg_number="RA-1", flag="RU", type_plane="A320", latitude=1.0, longitude=2.0, alt=1000
        )
    ]


async def _with_user_and_search_area(session) -> None:
    user_repo = UserRepository(session)
    await user_repo.get_or_create(USER_ID, "Ivan")
    await user_repo.set_location(USER_ID, 55.75, 37.62)
    bbox = BBox(min_lat=55.0, min_lon=37.0, max_lat=56.0, max_lon=38.0)
    await user_repo.set_search_area(USER_ID, bbox)


async def test_draw_requires_data_when_no_aircraft(session):
    await _with_user_and_search_area(session)
    message = _FakeMessage()

    await draw.draw(message, session)

    assert message.answers == [draw._NO_DATA_HINT]
    assert message.photos == []


async def test_draw_renders_and_sends_photo(session, monkeypatch):
    await _with_user_and_search_area(session)
    await AircraftRepository(session).replace_all(USER_ID, _one_aircraft())

    async def fake_render_map(user_lat, user_lon, aircraft, bbox):
        assert (user_lat, user_lon) == (55.75, 37.62)
        assert aircraft == [(1.0, 2.0)]
        return b"\x89PNGfakebytes"

    monkeypatch.setattr(draw, "render_map", fake_render_map)
    message = _FakeMessage()

    await draw.draw(message, session)

    assert len(message.photos) == 1
    assert message.photos[0].data == b"\x89PNGfakebytes"
    assert any("что дальше" in answer for answer in message.answers)


async def test_draw_reports_render_failure(session, monkeypatch):
    await _with_user_and_search_area(session)
    await AircraftRepository(session).replace_all(USER_ID, _one_aircraft())

    async def failing_render_map(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(draw, "render_map", failing_render_map)
    message = _FakeMessage()

    await draw.draw(message, session)

    assert message.photos == []
    assert message.answers == ["Что-то пошло не так, попробуйте еще раз"]
