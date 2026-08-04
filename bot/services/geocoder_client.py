from dataclasses import dataclass

import httpx

CLEAN_ADDRESS_URL = "https://cleaner.dadata.ru/api/v1/clean/address"


class GeocodingError(Exception):
    pass


@dataclass(frozen=True)
class GeocodeResult:
    lat: float | None
    lon: float | None
    result: str | None


class DadataClient:
    def __init__(
        self, token: str, secret_key: str, client: httpx.AsyncClient | None = None
    ) -> None:
        self._token = token
        self._secret_key = secret_key
        self._client = client or httpx.AsyncClient()

    async def geocode(self, address: str) -> GeocodeResult:
        headers = {
            "Authorization": f"Token {self._token}",
            "X-Secret": self._secret_key,
            "Content-Type": "application/json",
        }
        try:
            response = await self._client.post(CLEAN_ADDRESS_URL, json=[address], headers=headers)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise GeocodingError(f"DaData request failed: {error}") from error

        if not payload:
            raise GeocodingError("DaData returned an empty response")

        item = payload[0]
        lat = item.get("geo_lat")
        lon = item.get("geo_lon")
        return GeocodeResult(
            lat=float(lat) if lat is not None else None,
            lon=float(lon) if lon is not None else None,
            result=item.get("result"),
        )

    async def aclose(self) -> None:
        await self._client.aclose()
