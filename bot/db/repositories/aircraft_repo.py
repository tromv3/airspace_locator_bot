from collections.abc import Iterable
from collections.abc import Sequence as TypingSequence

from sqlalchemy import ColumnElement, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Aircraft
from bot.services.flight_types import AircraftInfo


class AircraftRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_all(self, user_id: int, aircraft: Iterable[AircraftInfo]) -> None:
        await self._session.execute(delete(Aircraft).where(Aircraft.user_id == user_id))
        self._session.add_all(
            Aircraft(
                user_id=user_id,
                reg_number=item.reg_number,
                flag=item.flag,
                type_plane=item.type_plane,
                latitude=item.latitude,
                longitude=item.longitude,
                alt=item.alt,
                source=item.source,
            )
            for item in aircraft
        )
        await self._session.flush()

    async def list_for_user(
        self,
        user_id: int,
        *,
        alt_min: int | None = None,
        alt_max: int | None = None,
        types: TypingSequence[str] | None = None,
        flags: TypingSequence[str] | None = None,
    ) -> list[Aircraft]:
        conditions = self._build_conditions(user_id, alt_min, alt_max, types, flags)
        # Deterministic order so a list numbered "1, 2, 3..." (`filters_show`)
        # lines up with the same numbers plotted on the map (`filters_draw`).
        result = await self._session.execute(
            select(Aircraft).where(*conditions).order_by(Aircraft.id)
        )
        return list(result.scalars())

    async def count_for_user(
        self,
        user_id: int,
        *,
        alt_min: int | None = None,
        alt_max: int | None = None,
        types: TypingSequence[str] | None = None,
        flags: TypingSequence[str] | None = None,
    ) -> int:
        conditions = self._build_conditions(user_id, alt_min, alt_max, types, flags)
        result = await self._session.execute(
            select(func.count()).select_from(Aircraft).where(*conditions)
        )
        return result.scalar_one()

    def _build_conditions(
        self,
        user_id: int,
        alt_min: int | None,
        alt_max: int | None,
        types: TypingSequence[str] | None,
        flags: TypingSequence[str] | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [Aircraft.user_id == user_id]
        if alt_min is not None:
            conditions.append(Aircraft.alt >= alt_min)
        if alt_max is not None:
            conditions.append(Aircraft.alt <= alt_max)
        if types:
            conditions.append(func.upper(Aircraft.type_plane).in_([t.upper() for t in types]))
        if flags:
            conditions.append(func.upper(Aircraft.flag).in_([f.upper() for f in flags]))
        return conditions

    async def get_by_id(self, aircraft_id: int) -> Aircraft | None:
        return await self._session.get(Aircraft, aircraft_id)

    async def distinct_types(self, user_id: int) -> set[str]:
        result = await self._session.execute(
            select(Aircraft.type_plane).where(
                Aircraft.user_id == user_id, Aircraft.type_plane.is_not(None)
            )
        )
        return {value.upper() for value in result.scalars()}

    async def distinct_flags(self, user_id: int) -> set[str]:
        result = await self._session.execute(
            select(Aircraft.flag).where(Aircraft.user_id == user_id, Aircraft.flag.is_not(None))
        )
        return set(result.scalars())
