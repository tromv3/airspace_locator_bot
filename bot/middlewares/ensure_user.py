from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.db.repositories.user_repo import UserRepository


class EnsureUserMiddleware(BaseMiddleware):
    """Create the user row on first contact, whatever the first update is.

    Handlers other than /start assume the user exists; without this a fresh
    database (or a chat with a leftover keyboard from an earlier bot) makes
    them crash on the first button press.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = getattr(event, "from_user", None)
        session = data.get("session")
        if from_user is not None and session is not None:
            full_name = " ".join(
                part for part in (from_user.first_name, from_user.last_name) if part
            )
            await UserRepository(session).get_or_create(from_user.id, full_name)
        return await handler(event, data)
