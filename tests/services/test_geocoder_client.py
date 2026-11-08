import json

import httpx
import pytest
import respx

from bot.services.geocoder_client import CLEAN_ADDRESS_URL, DadataClient, GeocodingError


@pytest.fixture
def client():
    return DadataClient(token="test-token", secret_key="test-secret")


@respx.mock
async def test_geocode_parses_successful_response(client):
    respx.post(CLEAN_ADDRESS_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "result": "г Москва, ул Рабочая, д 36",
                    "geo_lat": "55.744",
                    "geo_lon": "37.673",
                    "qc_geo": 0,
                }
            ],
        )
    )

    result = await client.geocode("москва рабочая 36")

    assert result.lat == 55.744
    assert result.lon == 37.673
    assert result.result == "г Москва, ул Рабочая, д 36"


@respx.mock
async def test_geocode_handles_unresolved_address(client):
    respx.post(CLEAN_ADDRESS_URL).mock(
        return_value=httpx.Response(
            200, json=[{"result": "полная дичь", "geo_lat": None, "geo_lon": None}]
        )
    )

    result = await client.geocode("полная дичь")

    assert result.lat is None
    assert result.lon is None


@respx.mock
async def test_geocode_sends_auth_headers_and_address_body(client):
    route = respx.post(CLEAN_ADDRESS_URL).mock(
        return_value=httpx.Response(200, json=[{"result": "x", "geo_lat": "1", "geo_lon": "2"}])
    )

    await client.geocode("москва рабочая 36")

    request = route.calls.last.request
    assert request.headers["Authorization"] == "Token test-token"
    assert request.headers["X-Secret"] == "test-secret"
    assert json.loads(request.content) == ["москва рабочая 36"]


@respx.mock
async def test_geocode_raises_on_empty_response(client):
    respx.post(CLEAN_ADDRESS_URL).mock(return_value=httpx.Response(200, json=[]))

    with pytest.raises(GeocodingError):
        await client.geocode("москва рабочая 36")


@respx.mock
async def test_geocode_raises_on_http_error(client):
    respx.post(CLEAN_ADDRESS_URL).mock(return_value=httpx.Response(403, json={}))

    with pytest.raises(GeocodingError):
        await client.geocode("москва рабочая 36")


@respx.mock
async def test_geocode_raises_on_network_error(client):
    respx.post(CLEAN_ADDRESS_URL).mock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(GeocodingError):
        await client.geocode("москва рабочая 36")
