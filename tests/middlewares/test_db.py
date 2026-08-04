import pytest

from bot.db.repositories.user_repo import UserRepository
from bot.middlewares.db import DbSessionMiddleware


class _FailingHandlerError(Exception):
    pass


async def test_commits_on_success(session):
    session_maker = _StaticSessionMaker(session)
    middleware = DbSessionMiddleware(session_maker)

    async def handler(event, data):
        await UserRepository(data["session"]).get_or_create(1, "Ivan")
        return "ok"

    result = await middleware(handler, event=object(), data={})

    assert result == "ok"
    assert await UserRepository(session).get(1) is not None


async def test_rolls_back_on_exception(session):
    session_maker = _StaticSessionMaker(session)
    middleware = DbSessionMiddleware(session_maker)

    async def handler(event, data):
        await UserRepository(data["session"]).get_or_create(1, "Ivan")
        raise _FailingHandlerError

    with pytest.raises(_FailingHandlerError):
        await middleware(handler, event=object(), data={})

    assert await UserRepository(session).get(1) is None


class _StaticSessionMaker:
    """Test double returning the shared in-memory `session` fixture as an async context manager."""

    def __init__(self, session):
        self._session = session

    def __call__(self):
        return self

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *exc_info):
        return False
