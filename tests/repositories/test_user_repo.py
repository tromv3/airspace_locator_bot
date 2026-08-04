from bot.db.repositories.user_repo import UserRepository
from bot.services.geo_math import BBox


async def test_get_returns_none_for_unknown_user(session):
    repo = UserRepository(session)

    assert await repo.get(1) is None


async def test_get_or_create_creates_once(session):
    repo = UserRepository(session)

    created = await repo.get_or_create(1, "Ivan Petrov")
    fetched = await repo.get_or_create(1, "Someone Else")

    assert created.id == 1
    assert created.name == "Ivan Petrov"
    assert fetched.name == "Ivan Petrov"  # second call doesn't overwrite


async def test_set_name(session):
    repo = UserRepository(session)
    await repo.get_or_create(1, "Old Name")

    await repo.set_name(1, "New Name")

    assert (await repo.get(1)).name == "New Name"


async def test_set_location(session):
    repo = UserRepository(session)
    await repo.get_or_create(1, "Ivan")

    await repo.set_location(1, 55.7558, 37.6173)

    user = await repo.get(1)
    assert user.location_lat == 55.7558
    assert user.location_lon == 37.6173


async def test_set_search_area_sets_bbox_and_last_req(session):
    repo = UserRepository(session)
    await repo.get_or_create(1, "Ivan")
    bbox = BBox(min_lat=55.0, min_lon=37.0, max_lat=56.0, max_lon=38.0)

    await repo.set_search_area(1, bbox)

    user = await repo.get(1)
    assert user.bbox_min_lat == 55.0
    assert user.bbox_min_lon == 37.0
    assert user.bbox_max_lat == 56.0
    assert user.bbox_max_lon == 38.0
    assert user.last_req is not None
