from bot.db.repositories.aircraft_repo import AircraftRepository
from bot.db.repositories.user_repo import UserRepository
from bot.services.flight_types import AircraftInfo

USER_ID = 1

SAMPLE_AIRCRAFT = [
    AircraftInfo(
        reg_number="RA-11111",
        flag="RU",
        type_plane="a320",
        latitude=55.1,
        longitude=37.1,
        alt=9000,
        source="airlabs",
    ),
    AircraftInfo(
        reg_number="RA-22222",
        flag="DE",
        type_plane="B738",
        latitude=55.2,
        longitude=37.2,
        alt=3000,
        source="airlabs",
    ),
    AircraftInfo(
        reg_number="RA-33333",
        flag="RU",
        type_plane="b738",
        latitude=55.3,
        longitude=37.3,
        alt=1000,
        source="opensky",
    ),
]


async def _seeded_repo(session) -> AircraftRepository:
    await UserRepository(session).get_or_create(USER_ID, "Ivan")
    repo = AircraftRepository(session)
    await repo.replace_all(USER_ID, SAMPLE_AIRCRAFT)
    return repo


async def test_replace_all_stores_aircraft(session):
    repo = await _seeded_repo(session)

    stored = await repo.list_for_user(USER_ID)

    assert len(stored) == 3
    assert {a.reg_number for a in stored} == {"RA-11111", "RA-22222", "RA-33333"}


async def test_replace_all_stores_source(session):
    repo = await _seeded_repo(session)

    stored = {a.reg_number: a.source for a in await repo.list_for_user(USER_ID)}

    assert stored["RA-11111"] == "airlabs"
    assert stored["RA-33333"] == "opensky"


async def test_replace_all_clears_previous_aircraft(session):
    repo = await _seeded_repo(session)

    await repo.replace_all(USER_ID, SAMPLE_AIRCRAFT[:1])

    assert await repo.count_for_user(USER_ID) == 1


async def test_count_for_user(session):
    repo = await _seeded_repo(session)

    assert await repo.count_for_user(USER_ID) == 3


async def test_list_for_user_filters_by_altitude_range(session):
    repo = await _seeded_repo(session)

    remaining = await repo.list_for_user(USER_ID, alt_min=2000, alt_max=5000)

    assert {a.reg_number for a in remaining} == {"RA-22222"}


async def test_list_for_user_filters_by_type_case_insensitively(session):
    repo = await _seeded_repo(session)

    remaining = await repo.list_for_user(USER_ID, types=["b738"])

    assert {a.reg_number for a in remaining} == {"RA-22222", "RA-33333"}


async def test_list_for_user_filters_by_flag(session):
    repo = await _seeded_repo(session)

    remaining = await repo.list_for_user(USER_ID, flags=["ru"])

    assert {a.reg_number for a in remaining} == {"RA-11111", "RA-33333"}


async def test_list_for_user_combines_filters(session):
    repo = await _seeded_repo(session)

    remaining = await repo.list_for_user(USER_ID, flags=["RU"], types=["B738"])

    assert {a.reg_number for a in remaining} == {"RA-33333"}


async def test_filtering_does_not_delete_rows(session):
    repo = await _seeded_repo(session)

    await repo.list_for_user(USER_ID, types=["A320"])

    assert await repo.count_for_user(USER_ID) == 3


async def test_count_for_user_applies_same_filters(session):
    repo = await _seeded_repo(session)

    assert await repo.count_for_user(USER_ID, alt_min=5000) == 1


async def test_distinct_types_are_uppercased(session):
    repo = await _seeded_repo(session)

    assert await repo.distinct_types(USER_ID) == {"A320", "B738"}


async def test_distinct_flags(session):
    repo = await _seeded_repo(session)

    assert await repo.distinct_flags(USER_ID) == {"RU", "DE"}
