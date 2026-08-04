from collections.abc import Iterable

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Aircraft
from bot.services.airlabs_client import AircraftInfo


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
            )
            for item in aircraft
        )
        await self._session.flush()

    async def list_for_user(self, user_id: int) -> list[Aircraft]:
        result = await self._session.execute(select(Aircraft).where(Aircraft.user_id == user_id))
        return list(result.scalars())

    async def count_for_user(self, user_id: int) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Aircraft).where(Aircraft.user_id == user_id)
        )
        return result.scalar_one()

    async def delete_where_alt_gte(self, user_id: int, value: int) -> None:
        await self._session.execute(
            delete(Aircraft).where(Aircraft.user_id == user_id, Aircraft.alt >= value)
        )

    async def delete_where_alt_lte(self, user_id: int, value: int) -> None:
        await self._session.execute(
            delete(Aircraft).where(Aircraft.user_id == user_id, Aircraft.alt <= value)
        )

    async def delete_where_type_not(self, user_id: int, type_plane: str) -> None:
        # Case-insensitive compare: stored casing comes verbatim from AirLabs,
        # while the filter value is whatever the user typed.
        await self._session.execute(
            delete(Aircraft).where(
                Aircraft.user_id == user_id,
                func.upper(Aircraft.type_plane) != type_plane.upper(),
            )
        )

    async def delete_where_flag_not(self, user_id: int, flag: str) -> None:
        await self._session.execute(
            delete(Aircraft).where(
                Aircraft.user_id == user_id, func.upper(Aircraft.flag) != flag.upper()
            )
        )

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
