import pytest
from PIL import Image
from staticmap import StaticMap

from bot.services.geo_math import BBox
from bot.services.map_renderer import render_map


@pytest.fixture(autouse=True)
def mock_tile_render(monkeypatch):
    """Stub out the network tile fetch; capture markers/lines added before rendering."""
    captured = {}

    def fake_render(self, zoom=None, center=None):
        captured["markers"] = list(self.markers)
        captured["lines"] = list(self.lines)
        return Image.new("RGB", (10, 10))

    monkeypatch.setattr(StaticMap, "render", fake_render)
    return captured


async def test_render_map_adds_user_and_aircraft_markers(mock_tile_render):
    bbox = BBox(min_lat=55.0, min_lon=37.0, max_lat=56.0, max_lon=38.0)

    png_bytes = await render_map(55.5, 37.5, [(55.6, 37.6), (55.4, 37.4)], bbox)

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
