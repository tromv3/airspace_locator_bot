from __future__ import annotations

import datetime

from sqlalchemy import BigInteger, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base


class User(Base):
    __tablename__ = "users"

    # Telegram user id used directly as PK (no separate surrogate key needed).
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(default=None)

    location_lat: Mapped[float | None] = mapped_column(default=None)
    location_lon: Mapped[float | None] = mapped_column(default=None)

    bbox_min_lat: Mapped[float | None] = mapped_column(default=None)
    bbox_min_lon: Mapped[float | None] = mapped_column(default=None)
    bbox_max_lat: Mapped[float | None] = mapped_column(default=None)
    bbox_max_lon: Mapped[float | None] = mapped_column(default=None)

    last_req: Mapped[datetime.datetime | None] = mapped_column(default=None)

    aircraft: Mapped[list[Aircraft]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    history: Mapped[list[History]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return str(self.name)


class Aircraft(Base):
    __tablename__ = "aircraft"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    reg_number: Mapped[str | None] = mapped_column(default=None)
    flag: Mapped[str | None] = mapped_column(default=None)
    type_plane: Mapped[str | None] = mapped_column(default=None)
    latitude: Mapped[float | None] = mapped_column(default=None)
    longitude: Mapped[float | None] = mapped_column(default=None)
    alt: Mapped[int | None] = mapped_column(default=None)

    user: Mapped[User] = relationship(back_populates="aircraft")


class History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    command: Mapped[str | None] = mapped_column(default=None)
    date: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    user: Mapped[User] = relationship(back_populates="history")
