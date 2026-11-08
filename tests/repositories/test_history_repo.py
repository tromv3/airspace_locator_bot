from bot.db.repositories.history_repo import HistoryRepository
from bot.db.repositories.user_repo import UserRepository

USER_ID = 1


async def _with_user(session) -> HistoryRepository:
    await UserRepository(session).get_or_create(USER_ID, "Ivan")
    return HistoryRepository(session)


async def test_add_and_list_for_user(session):
    repo = await _with_user(session)

    await repo.add(USER_ID, "Запустить бота")
    await repo.add(USER_ID, "Изменить местоположение")

    history = await repo.list_for_user(USER_ID)
    assert [h.command for h in history] == ["Запустить бота", "Изменить местоположение"]


async def test_list_for_user_is_empty_for_unknown_user(session):
    repo = await _with_user(session)

    assert await repo.list_for_user(999) == []


async def test_add_trims_older_entries_beyond_limit(session, monkeypatch):
    monkeypatch.setattr("bot.db.repositories.history_repo.HISTORY_LIMIT", 3)
    repo = await _with_user(session)

    for i in range(5):
        await repo.add(USER_ID, f"cmd{i}")

    history = await repo.list_for_user(USER_ID)
    assert [h.command for h in history] == ["cmd2", "cmd3", "cmd4"]
