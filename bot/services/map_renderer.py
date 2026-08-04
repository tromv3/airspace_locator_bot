import asyncio
from io import BytesIO

from staticmap import CircleMarker, Line, StaticMap

from bot.services.geo_math import BBox

MAP_WIDTH = 800
MAP_HEIGHT = 600

USER_MARKER_COLOR = "green"
USER_MARKER_WIDTH = 12
AIRCRAFT_MARKER_COLOR = "blue"
AIRCRAFT_MARKER_WIDTH = 8
BBOX_LINE_COLOR = "red"
BBOX_LINE_WIDTH = 2

# OSM tile usage policy requires an identifying User-Agent with contact info:
# https://operations.osmfoundation.org/policies/tiles/ — fill in the repo URL
# before deploying, don't put a personal email here.
TILE_USER_AGENT = "airspace-locator-bot (+https://github.com/<your-username>/airspace-locator_bot)"


async def render_map(
    user_lat: float,
    user_lon: float,
    aircraft: list[tuple[float, float]],
    bbox: BBox,
) -> bytes:
    return await asyncio.to_thread(_render_map_sync, user_lat, user_lon, aircraft, bbox)


def _render_map_sync(
    user_lat: float,
    user_lon: float,
    aircraft: list[tuple[float, float]],
    bbox: BBox,
) -> bytes:
    static_map = StaticMap(MAP_WIDTH, MAP_HEIGHT, headers={"User-Agent": TILE_USER_AGENT})

    static_map.add_line(Line(_bbox_outline(bbox), BBOX_LINE_COLOR, BBOX_LINE_WIDTH))
    for lat, lon in aircraft:
        marker = CircleMarker((lon, lat), AIRCRAFT_MARKER_COLOR, AIRCRAFT_MARKER_WIDTH)
        static_map.add_marker(marker)
    static_map.add_marker(CircleMarker((user_lon, user_lat), USER_MARKER_COLOR, USER_MARKER_WIDTH))

    image = static_map.render()
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _bbox_outline(bbox: BBox) -> list[tuple[float, float]]:
    return [
        (bbox.min_lon, bbox.min_lat),
        (bbox.max_lon, bbox.min_lat),
        (bbox.max_lon, bbox.max_lat),
        (bbox.min_lon, bbox.max_lat),
        (bbox.min_lon, bbox.min_lat),
    ]
