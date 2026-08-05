from dataclasses import dataclass


@dataclass(frozen=True)
class AircraftInfo:
    reg_number: str | None
    flag: str | None
    type_plane: str | None
    latitude: float | None
    longitude: float | None
    alt: int | None
    source: str
