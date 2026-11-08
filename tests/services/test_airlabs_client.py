import httpx
import pytest
import respx

from bot.services.airlabs_client import AirLabsClient, AirLabsError
from bot.services.geo_math import BBox

BBOX = BBox(min_lat=55.0, min_lon=37.0, max_lat=56.0, max_lon=38.0)


@pytest.fixture
def client():
    return AirLabsClient(api_key="test-key")


@respx.mock
async def test_get_flights_parses_response(client):
    respx.get("https://airlabs.co/api/v9/flights").mock(
        return_value=httpx.Response(
            200,
            json={
                "response": [
                    {
                        "reg_number": "RA-12345",
                        "flag": "RU",
                        "aircraft_icao": "A320",
                        "lat": 55.5,
                        "lng": 37.5,
                        "alt": 10000,
                    },
                    {"reg_number": "N54321"},
                ]
            },
        )
    )

    aircraft = await client.get_flights(BBOX)

    assert len(aircraft) == 2
    assert aircraft[0].reg_number == "RA-12345"
    assert aircraft[0].type_plane == "A320"
    assert aircraft[0].latitude == 55.5
    assert aircraft[1].reg_number == "N54321"
    assert aircraft[1].flag is None


@respx.mock
async def test_get_flights_sends_rounded_bbox_and_api_key(client):
    route = respx.get("https://airlabs.co/api/v9/flights").mock(
        return_value=httpx.Response(200, json={"response": []})
    )

    await client.get_flights(BBox(min_lat=55.123456, min_lon=37.1, max_lat=56.9, max_lon=38.1))

    request = route.calls.last.request
    params = httpx.QueryParams(request.url.query)
    assert params["api_key"] == "test-key"
    assert params["bbox"] == "55.12,37.1,56.9,38.1"


@respx.mock
async def test_get_flights_raises_on_api_error(client):
    respx.get("https://airlabs.co/api/v9/flights").mock(
        return_value=httpx.Response(200, json={"error": {"message": "invalid_api_key"}})
    )

    with pytest.raises(AirLabsError, match="invalid_api_key"):
        await client.get_flights(BBOX)


@respx.mock
async def test_get_flights_raises_on_http_error_status(client):
    respx.get("https://airlabs.co/api/v9/flights").mock(return_value=httpx.Response(500, json={}))

    with pytest.raises(AirLabsError):
        await client.get_flights(BBOX)


@respx.mock
async def test_get_flights_raises_on_network_error(client):
    respx.get("https://airlabs.co/api/v9/flights").mock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(AirLabsError):
        await client.get_flights(BBOX)
