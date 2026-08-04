from dataclasses import dataclass

import httpx

from bot.services.geo_math import BBox

BASE_URL = "https://airlabs.co/api/v9/"


class AirLabsError(Exception):
    pass


@dataclass(frozen=True)
class AircraftInfo:
    reg_number: str | None
    flag: str | None
    type_plane: str | None
    latitude: float | None
    longitude: float | None
    alt: int | None


class AirLabsClient:
    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(base_url=BASE_URL)

    async def get_flights(self, bbox: BBox) -> list[AircraftInfo]:
        params = {
            "api_key": self._api_key,
            "bbox": ",".join(
                str(round(coordinate, 2))
                for coordinate in (bbox.min_lat, bbox.min_lon, bbox.max_lat, bbox.max_lon)
            ),
        }
        try:
            response = await self._client.get("flights", params=params)
            payload = response.json()
        except httpx.HTTPError as error:
            raise AirLabsError(f"AirLabs request failed: {error}") from error

        if "error" in payload:
            raise AirLabsError(payload["error"].get("message", "unknown AirLabs error"))
        if response.status_code != 200:
            raise AirLabsError(f"AirLabs returned HTTP {response.status_code}")

        return [_aircraft_from_payload(item) for item in payload.get("response", [])]

    async def aclose(self) -> None:
        await self._client.aclose()


def _aircraft_from_payload(item: dict) -> AircraftInfo:
    return AircraftInfo(
        reg_number=item.get("reg_number"),
        flag=item.get("flag"),
        type_plane=item.get("aircraft_icao"),
        latitude=item.get("lat"),
        longitude=item.get("lng"),
        alt=item.get("alt"),
    )
