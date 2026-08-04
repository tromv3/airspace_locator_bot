import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User
from bot.services.geo_math import BBox


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_or_create(self, user_id: int, name: str | None) -> User:
        user = await self.get(user_id)
        if user is None:
            user = User(id=user_id, name=name)
            self._session.add(user)
            await self._session.flush()
        return user

    async def set_name(self, user_id: int, name: str | None) -> None:
        user = await self.get(user_id)
        user.name = name

    async def set_location(self, user_id: int, lat: float, lon: float) -> None:
        user = await self.get(user_id)
        user.location_lat = lat
        user.location_lon = lon

    async def set_search_area(self, user_id: int, bbox: BBox) -> None:
        user = await self.get(user_id)
        user.bbox_min_lat = bbox.min_lat
        user.bbox_min_lon = bbox.min_lon
        user.bbox_max_lat = bbox.max_lat
        user.bbox_max_lon = bbox.max_lon
        user.last_req = datetime.datetime.now()
