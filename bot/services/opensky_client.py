import httpx

from bot.services.flight_types import AircraftInfo
from bot.services.geo_math import BBox

BASE_URL = "https://opensky-network.org/api/"

# AirLabs already reports altitude in feet; OpenSky reports meters, so fallback
# results need this conversion or altitude filtering would silently misbehave.
_METERS_TO_FEET = 3.28084


class OpenSkyError(Exception):
    pass


class OpenSkyClient:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(base_url=BASE_URL)

    async def get_flights(self, bbox: BBox) -> list[AircraftInfo]:
        params = {
            "lamin": bbox.min_lat,
            "lomin": bbox.min_lon,
            "lamax": bbox.max_lat,
            "lomax": bbox.max_lon,
        }
        try:
            response = await self._client.get("states/all", params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise OpenSkyError(f"OpenSky request failed: {error}") from error

        return [_aircraft_from_state(state) for state in payload.get("states") or []]

    async def aclose(self) -> None:
        await self._client.aclose()


def _aircraft_from_state(state: list) -> AircraftInfo:
    # Positional array per OpenSky's /states/all spec: index 1 = callsign,
    # 2 = origin_country, 5/6 = longitude/latitude, 7 = baro_altitude (m),
    # 13 = geo_altitude (m) as a fallback when baro_altitude is missing.
    callsign = (state[1] or "").strip() if len(state) > 1 else ""
    altitude_m = state[7] if len(state) > 7 else None
    if altitude_m is None and len(state) > 13:
        altitude_m = state[13]

    return AircraftInfo(
        reg_number=callsign or None,
        flag=state[2] if len(state) > 2 else None,
        type_plane=None,
        longitude=state[5] if len(state) > 5 else None,
        latitude=state[6] if len(state) > 6 else None,
        alt=round(altitude_m * _METERS_TO_FEET) if altitude_m is not None else None,
        source="opensky",
    )
