from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.constants import HISTORY_LIMIT
from bot.db.models import History


class HistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user_id: int, command: str) -> None:
        self._session.add(History(user_id=user_id, command=command))
        await self._session.flush()
        await self._trim(user_id)

    async def list_for_user(self, user_id: int) -> list[History]:
        result = await self._session.execute(
            select(History)
            .where(History.user_id == user_id)
            .order_by(History.date, History.id)
        )
        return list(result.scalars())

    async def _trim(self, user_id: int) -> None:
        # Keep only the most recent HISTORY_LIMIT rows for this user. `date` has
        # only second resolution (sqlite CURRENT_TIMESTAMP), so break ties by id
        # to keep ordering deterministic for rows added within the same second.
        result = await self._session.execute(
            select(History.id)
            .where(History.user_id == user_id)
            .order_by(History.date.desc(), History.id.desc())
            .offset(HISTORY_LIMIT)
        )
        stale_ids = list(result.scalars())
        if stale_ids:
            await self._session.execute(delete(History).where(History.id.in_(stale_ids)))
