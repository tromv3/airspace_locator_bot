from io import BytesIO

import pytest
from PIL import Image
from staticmap import StaticMap
from staticmap.staticmap import _lat_to_y, _lon_to_x

from bot.services.geo_math import BBox
from bot.services.map_renderer import AircraftPoint, render_map

_CENTER_LAT = 55.5
_CENTER_LON = 37.5
_ZOOM = 10


@pytest.fixture(autouse=True)
def mock_tile_render(monkeypatch):
    """Stub out the network tile fetch; capture markers/lines added before rendering.

    Centers the map on (_CENTER_LAT, _CENTER_LON) so pixel-placement math (used
    both by staticmap's own markers and this project's label/legend drawing)
    lands points near canvas center instead of off-screen.
    """
    captured = {}

    def fake_render(self, zoom=None, center=None):
        captured["markers"] = list(self.markers)
        captured["lines"] = list(self.lines)
        self.zoom = _ZOOM
        self.x_center = _lon_to_x(_CENTER_LON, _ZOOM)
        self.y_center = _lat_to_y(_CENTER_LAT, _ZOOM)
        return Image.new("RGB", (800, 600), "white")

    monkeypatch.setattr(StaticMap, "render", fake_render)
    return captured


async def test_render_map_adds_user_and_aircraft_markers(mock_tile_render):
    bbox = BBox(min_lat=55.0, min_lon=37.0, max_lat=56.0, max_lon=38.0)
    aircraft = [
        AircraftPoint(lat=55.6, lon=37.6, label="RA-1"),
        AircraftPoint(lat=55.4, lon=37.4, label="RA-2"),
    ]

    png_bytes = await render_map(55.5, 37.5, aircraft, bbox)

    assert png_bytes.startswith(b"\x89PNG")
    markers = mock_tile_render["markers"]
    assert len(markers) == 3  # 2 aircraft + 1 user
    assert markers[-1].coord == (37.5, 55.5)  # user marker added last, coord is (lon, lat)
    assert len(mock_tile_render["lines"]) == 1


async def test_render_map_bbox_outline_is_closed_rectangle(mock_tile_render):
    bbox = BBox(min_lat=10.0, min_lon=20.0, max_lat=11.0, max_lon=21.0)

    await render_map(10.5, 20.5, [], bbox)

    line = mock_tile_render["lines"][0]
    assert line.coords[0] == line.coords[-1]
    assert set(line.coords) == {(20.0, 10.0), (21.0, 10.0), (21.0, 11.0), (20.0, 11.0)}


async def test_render_map_draws_legend_over_blank_canvas(mock_tile_render):
    bbox = BBox(min_lat=55.0, min_lon=37.0, max_lat=56.0, max_lon=38.0)

    png_bytes = await render_map(_CENTER_LAT, _CENTER_LON, [], bbox)
    rendered = Image.open(BytesIO(png_bytes)).convert("RGBA")

    # the legend's aircraft-color dot should be visible near its known offset
    # from the top-left corner, distinctly bluer than the blank white canvas.
    red, green, blue, _ = rendered.getpixel((18, 20))
    assert blue > 150
    assert red < 100 and green < 100


async def test_render_map_draws_label_near_aircraft_marker(mock_tile_render):
    bbox = BBox(min_lat=55.0, min_lon=37.0, max_lat=56.0, max_lon=38.0)

    without_label = await render_map(_CENTER_LAT, _CENTER_LON, [], bbox)
    with_label = await render_map(
        _CENTER_LAT,
        _CENTER_LON,
        [AircraftPoint(lat=_CENTER_LAT, lon=_CENTER_LON, label="RA-1")],
        bbox,
    )

    assert without_label != with_label
