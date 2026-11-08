import asyncio
from dataclasses import dataclass
from io import BytesIO

from PIL import ImageDraw, ImageFont
from staticmap import CircleMarker, StaticMap
from staticmap.staticmap import _lat_to_y, _lon_to_x

from bot.services.geo_math import BBox

MAP_WIDTH = 1000
MAP_HEIGHT = 750

USER_MARKER_COLOR = "green"
USER_MARKER_WIDTH = 12
AIRCRAFT_MARKER_COLOR = "blue"
AIRCRAFT_MARKER_WIDTH = 8
BBOX_LINE_COLOR = "red"
BBOX_LINE_WIDTH = 2

LABEL_FONT_SIZE = 18
LABEL_COLOR = "black"
LABEL_STROKE_COLOR = "white"
LABEL_STROKE_WIDTH = 2
LABEL_OFFSET_PX = (8, -11)

# OSM tile usage policy requires an identifying User-Agent with contact info:
# https://operations.osmfoundation.org/policies/tiles/ — repo URL, not a personal email.
TILE_USER_AGENT = "airspace-locator-bot (+https://github.com/tromv3/airspace_locator_bot)"


@dataclass(frozen=True)
class AircraftPoint:
    lat: float
    lon: float
    label: str


async def render_map(
    user_lat: float,
    user_lon: float,
    aircraft: list[AircraftPoint],
    bbox: BBox,
) -> bytes:
    return await asyncio.to_thread(_render_map_sync, user_lat, user_lon, aircraft, bbox)


def _render_map_sync(
    user_lat: float,
    user_lon: float,
    aircraft: list[AircraftPoint],
    bbox: BBox,
) -> bytes:
    static_map = StaticMap(MAP_WIDTH, MAP_HEIGHT, headers={"User-Agent": TILE_USER_AGENT})

    # Only markers (aircraft + user) drive the automatic zoom/center, not the
    # search-radius outline below - otherwise a wide search radius always
    # forces a zoomed-out view even when every aircraft is tightly clustered,
    # making individual points impossible to tell apart.
    for point in aircraft:
        marker = CircleMarker((point.lon, point.lat), AIRCRAFT_MARKER_COLOR, AIRCRAFT_MARKER_WIDTH)
        static_map.add_marker(marker)
    static_map.add_marker(CircleMarker((user_lon, user_lat), USER_MARKER_COLOR, USER_MARKER_WIDTH))

    image = static_map.render()
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=LABEL_FONT_SIZE)

    _draw_bbox_outline(draw, static_map, bbox)
    for point in aircraft:
        _draw_label(draw, static_map, point, font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _to_px(static_map: StaticMap, lon: float, lat: float) -> tuple[float, float]:
    # Pixel conversion mirrors staticmap's own marker placement
    # (StaticMap._draw_features), minus its internal 2x oversampling factor
    # since we're drawing on the already-rendered, final-size image.
    return (
        static_map._x_to_px(_lon_to_x(lon, static_map.zoom)),
        static_map._y_to_px(_lat_to_y(lat, static_map.zoom)),
    )


def _draw_bbox_outline(draw: ImageDraw.ImageDraw, static_map: StaticMap, bbox: BBox) -> None:
    points = [_to_px(static_map, lon, lat) for lon, lat in _bbox_outline(bbox)]
    draw.line(points, fill=BBOX_LINE_COLOR, width=BBOX_LINE_WIDTH)


def _draw_label(
    draw: ImageDraw.ImageDraw,
    static_map: StaticMap,
    point: AircraftPoint,
    font: ImageFont.ImageFont,
) -> None:
    x, y = _to_px(static_map, point.lon, point.lat)
    draw.text(
        (x + LABEL_OFFSET_PX[0], y + LABEL_OFFSET_PX[1]),
        point.label,
        font=font,
        fill=LABEL_COLOR,
        stroke_width=LABEL_STROKE_WIDTH,
        stroke_fill=LABEL_STROKE_COLOR,
    )


def _bbox_outline(bbox: BBox) -> list[tuple[float, float]]:
    return [
        (bbox.min_lon, bbox.min_lat),
        (bbox.max_lon, bbox.min_lat),
        (bbox.max_lon, bbox.max_lat),
        (bbox.min_lon, bbox.max_lat),
        (bbox.min_lon, bbox.min_lat),
    ]
