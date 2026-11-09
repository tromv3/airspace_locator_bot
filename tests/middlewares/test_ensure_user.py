from bot.db.repositories.user_repo import UserRepository
from bot.middlewares.ensure_user import EnsureUserMiddleware

USER_ID = 7


class _FakeUser:
    def __init__(self, user_id=USER_ID, first_name="Ivan", last_name=None):
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name


class _FakeEvent:
    def __init__(self, from_user):
        self.from_user = from_user


async def _run(session, event):
    calls = []

    async def handler(event, data):
        calls.append(data)
        return "handled"

    result = await EnsureUserMiddleware()(handler, event, {"session": session})
    return result, calls


async def test_creates_missing_user_before_handler_runs(session):
    result, calls = await _run(session, _FakeEvent(_FakeUser(last_name="Petrov")))

    assert result == "handled"
    assert len(calls) == 1
    user = await UserRepository(session).get(USER_ID)
    assert user is not None
    assert user.name == "Ivan Petrov"


async def test_does_not_overwrite_existing_user(session):
    await UserRepository(session).get_or_create(USER_ID, "Saved Name")

    await _run(session, _FakeEvent(_FakeUser(first_name="Other")))

    user = await UserRepository(session).get(USER_ID)
    assert user.name == "Saved Name"


async def test_skips_events_without_sender(session):
    result, calls = await _run(session, _FakeEvent(None))

    assert result == "handled"
    assert len(calls) == 1
