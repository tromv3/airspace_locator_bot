import httpx
import respx

from bot.services.planespotters_client import PlanespottersClient


@respx.mock
async def test_get_photo_url_returns_large_thumbnail():
    respx.get("https://api.planespotters.net/pub/photos/reg/RA-12345").mock(
        return_value=httpx.Response(
            200,
            json={
                "photos": [
                    {
                        "thumbnail": {"src": "https://example.com/small.jpg"},
                        "thumbnail_large": {"src": "https://example.com/large.jpg"},
                    }
                ]
            },
        )
    )
    client = PlanespottersClient()

    url = await client.get_photo_url("RA-12345")

    assert url == "https://example.com/large.jpg"


@respx.mock
async def test_get_photo_url_falls_back_to_small_thumbnail():
    respx.get("https://api.planespotters.net/pub/photos/reg/RA-12345").mock(
        return_value=httpx.Response(
            200, json={"photos": [{"thumbnail": {"src": "https://example.com/small.jpg"}}]}
        )
    )
    client = PlanespottersClient()

    url = await client.get_photo_url("RA-12345")

    assert url == "https://example.com/small.jpg"


@respx.mock
async def test_get_photo_url_returns_none_when_no_photos():
    respx.get("https://api.planespotters.net/pub/photos/reg/RA-12345").mock(
        return_value=httpx.Response(200, json={"photos": []})
    )
    client = PlanespottersClient()

    assert await client.get_photo_url("RA-12345") is None


@respx.mock
async def test_get_photo_url_returns_none_on_http_error():
    respx.get("https://api.planespotters.net/pub/photos/reg/RA-12345").mock(
        return_value=httpx.Response(500)
    )
    client = PlanespottersClient()

    assert await client.get_photo_url("RA-12345") is None


@respx.mock
async def test_get_photo_url_returns_none_on_network_error():
    respx.get("https://api.planespotters.net/pub/photos/reg/RA-12345").mock(
        side_effect=httpx.ConnectError("boom")
    )
    client = PlanespottersClient()

    assert await client.get_photo_url("RA-12345") is None
