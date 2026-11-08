import httpx
import pytest
import respx

from bot.services.geo_math import BBox
from bot.services.opensky_client import OpenSkyClient, OpenSkyError

BBOX = BBox(min_lat=55.0, min_lon=37.0, max_lat=56.0, max_lon=38.0)


@pytest.fixture
def client():
    return OpenSkyClient()


@respx.mock
async def test_get_flights_parses_states_and_converts_altitude(client):
    respx.get("https://opensky-network.org/api/states/all").mock(
        return_value=httpx.Response(
            200,
            json={
                "states": [
                    [
                        "abc123",
                        "RA-1   ",
                        "Russia",
                        None,
                        None,
                        37.5,
                        55.5,
                        3048.0,
                        False,
                        0,
                        0,
                        0,
                        None,
                        None,
                    ]
                ]
            },
        )
    )

    aircraft = await client.get_flights(BBOX)

    assert len(aircraft) == 1
    plane = aircraft[0]
    assert plane.reg_number == "RA-1"
    assert plane.flag == "Russia"
    assert plane.type_plane is None
    assert plane.latitude == 55.5
    assert plane.longitude == 37.5
    assert plane.alt == 10000  # 3048m -> ~10000ft
    assert plane.source == "opensky"


@respx.mock
async def test_get_flights_falls_back_to_geo_altitude(client):
    state = [None] * 14
    state[1] = "RA-2"
    state[2] = "Germany"
    state[5] = 37.5
    state[6] = 55.5
    state[7] = None
    state[13] = 1000.0
    respx.get("https://opensky-network.org/api/states/all").mock(
        return_value=httpx.Response(200, json={"states": [state]})
    )

    aircraft = await client.get_flights(BBOX)

    assert aircraft[0].alt == round(1000.0 * 3.28084)


@respx.mock
async def test_get_flights_handles_empty_callsign(client):
    state = [None] * 8
    state[1] = "   "
    respx.get("https://opensky-network.org/api/states/all").mock(
        return_value=httpx.Response(200, json={"states": [state]})
    )

    aircraft = await client.get_flights(BBOX)

    assert aircraft[0].reg_number is None


@respx.mock
async def test_get_flights_handles_no_states(client):
    respx.get("https://opensky-network.org/api/states/all").mock(
        return_value=httpx.Response(200, json={"states": None})
    )

    assert await client.get_flights(BBOX) == []


@respx.mock
async def test_get_flights_raises_on_http_error_status(client):
    respx.get("https://opensky-network.org/api/states/all").mock(
        return_value=httpx.Response(429)
    )

    with pytest.raises(OpenSkyError):
        await client.get_flights(BBOX)


@respx.mock
async def test_get_flights_raises_on_network_error(client):
    respx.get("https://opensky-network.org/api/states/all").mock(
        side_effect=httpx.ConnectError("boom")
    )

    with pytest.raises(OpenSkyError):
        await client.get_flights(BBOX)
