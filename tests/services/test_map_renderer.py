from io import BytesIO

import pytest
from PIL import Image
from staticmap import StaticMap
from staticmap.staticmap import _lat_to_y, _lon_to_x

from bot.services.geo_math import BBox
from bot.services.map_renderer import MAP_HEIGHT, MAP_WIDTH, AircraftPoint, render_map

_CENTER_LAT = 55.5
_CENTER_LON = 37.5
_ZOOM = 10


@pytest.fixture(autouse=True)
def mock_tile_render(monkeypatch):
    """Stub out the network tile fetch; capture markers added before rendering.

    Centers the map on (_CENTER_LAT, _CENTER_LON) so pixel-placement math (used
    both by staticmap's own markers and this project's label/outline drawing)
    lands points near canvas center instead of off-screen.
    """
    captured = {}

    def fake_render(self, zoom=None, center=None):
        captured["markers"] = list(self.markers)
        captured["lines"] = list(self.lines)
        self.zoom = _ZOOM
        self.x_center = _lon_to_x(_CENTER_LON, _ZOOM)
        self.y_center = _lat_to_y(_CENTER_LAT, _ZOOM)
        return Image.new("RGB", (MAP_WIDTH, MAP_HEIGHT), "white")

    monkeypatch.setattr(StaticMap, "render", fake_render)
    return captured


async def test_render_map_adds_user_and_aircraft_markers(mock_tile_render):
    bbox = BBox(min_lat=55.0, min_lon=37.0, max_lat=56.0, max_lon=38.0)
    aircraft = [
        AircraftPoint(lat=55.6, lon=37.6, label="1"),
        AircraftPoint(lat=55.4, lon=37.4, label="2"),
    ]

    png_bytes = await render_map(55.5, 37.5, aircraft, bbox)

    assert png_bytes.startswith(b"\x89PNG")
    markers = mock_tile_render["markers"]
    assert len(markers) == 3  # 2 aircraft + 1 user
    assert markers[-1].coord == (37.5, 55.5)  # user marker added last, coord is (lon, lat)
    # the search-radius outline is drawn by hand after render(), not passed as
    # a staticmap Line, so it never influences the automatic zoom/center.
    assert mock_tile_render["lines"] == []


async def test_render_map_zoom_ignores_search_radius(mock_tile_render):
    # A huge bbox (~300km+) must not prevent aircraft-only extent/zoom - the
    # renderer no longer feeds the outline into staticmap's auto-zoom.
    bbox = BBox(min_lat=53.0, min_lon=35.0, max_lat=58.0, max_lon=40.0)

    await render_map(55.5, 37.5, [AircraftPoint(lat=55.6, lon=37.6, label="1")], bbox)

    markers = mock_tile_render["markers"]
    assert len(markers) == 2
    assert mock_tile_render["lines"] == []


async def test_render_map_draws_bbox_outline(mock_tile_render):
    # This corner sits exactly at the map's center pixel given the fixture's
    # fake center/zoom, so the hand-drawn outline should be visibly red there.
    bbox = BBox(min_lat=_CENTER_LAT, min_lon=_CENTER_LON, max_lat=56.0, max_lon=38.0)

    png_bytes = await render_map(_CENTER_LAT, _CENTER_LON, [], bbox)
    rendered = Image.open(BytesIO(png_bytes)).convert("RGB")

    red, green, blue = rendered.getpixel((MAP_WIDTH // 2, MAP_HEIGHT // 2))
    assert red > 150
    assert green < 100 and blue < 100


async def test_render_map_draws_label_near_aircraft_marker(mock_tile_render):
    bbox = BBox(min_lat=55.0, min_lon=37.0, max_lat=56.0, max_lon=38.0)

    without_label = await render_map(_CENTER_LAT, _CENTER_LON, [], bbox)
    with_label = await render_map(
        _CENTER_LAT, _CENTER_LON, [AircraftPoint(lat=_CENTER_LAT, lon=_CENTER_LON, label="1")], bbox
    )

    assert without_label != with_label
