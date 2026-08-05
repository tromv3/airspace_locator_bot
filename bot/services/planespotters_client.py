import httpx

BASE_URL = "https://api.planespotters.net/pub/photos/reg/"


class PlanespottersClient:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(base_url=BASE_URL)

    async def get_photo_url(self, reg_number: str) -> str | None:
        # Photos are a decoration, not a required feature - any failure here
        # (network, unknown registration, no photo on file) should degrade
        # to no-photo, never raise and break the aircraft-info flow.
        try:
            response = await self._client.get(reg_number)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError:
            return None

        photos = payload.get("photos") or []
        if not photos:
            return None

        thumbnail = photos[0].get("thumbnail_large") or photos[0].get("thumbnail")
        return thumbnail.get("src") if thumbnail else None

    async def aclose(self) -> None:
        await self._client.aclose()
