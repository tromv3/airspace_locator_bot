import asyncio
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from staticmap import CircleMarker, Line, StaticMap
from staticmap.staticmap import _lat_to_y, _lon_to_x

from bot.services.geo_math import BBox

MAP_WIDTH = 800
MAP_HEIGHT = 600

USER_MARKER_COLOR = "green"
USER_MARKER_WIDTH = 12
AIRCRAFT_MARKER_COLOR = "blue"
AIRCRAFT_MARKER_WIDTH = 8
BBOX_LINE_COLOR = "red"
BBOX_LINE_WIDTH = 2

LABEL_COLOR = "black"
LABEL_OFFSET_PX = (6, -6)

LEGEND_MARGIN = 8
LEGEND_PADDING = 6
LEGEND_LINE_HEIGHT = 14
LEGEND_BACKGROUND = (255, 255, 255, 200)
LEGEND_ENTRIES = (
    (AIRCRAFT_MARKER_COLOR, "Воздушное судно"),
    (USER_MARKER_COLOR, "Вы"),
    (BBOX_LINE_COLOR, "Зона поиска"),
)

# OSM tile usage policy requires an identifying User-Agent with contact info:
# https://operations.osmfoundation.org/policies/tiles/ — fill in the repo URL
# before deploying, don't put a personal email here.
TILE_USER_AGENT = "airspace-locator-bot (+https://github.com/<your-username>/airspace-locator_bot)"


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

    static_map.add_line(Line(_bbox_outline(bbox), BBOX_LINE_COLOR, BBOX_LINE_WIDTH))
    for point in aircraft:
        marker = CircleMarker((point.lon, point.lat), AIRCRAFT_MARKER_COLOR, AIRCRAFT_MARKER_WIDTH)
        static_map.add_marker(marker)
    static_map.add_marker(CircleMarker((user_lon, user_lat), USER_MARKER_COLOR, USER_MARKER_WIDTH))

    image = static_map.render().convert("RGBA")
    font = ImageFont.load_default()

    draw = ImageDraw.Draw(image)
    for point in aircraft:
        _draw_label(draw, static_map, point, font)

    _draw_legend(image, font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _draw_label(
    draw: ImageDraw.ImageDraw,
    static_map: StaticMap,
    point: AircraftPoint,
    font: ImageFont.ImageFont,
) -> None:
    # Pixel conversion mirrors staticmap's own marker placement
    # (StaticMap._draw_features), minus its internal 2x oversampling factor
    # since we're drawing on the already-rendered, final-size image.
    x = static_map._x_to_px(_lon_to_x(point.lon, static_map.zoom))
    y = static_map._y_to_px(_lat_to_y(point.lat, static_map.zoom))
    draw.text(
        (x + LABEL_OFFSET_PX[0], y + LABEL_OFFSET_PX[1]), point.label, fill=LABEL_COLOR, font=font
    )


def _draw_legend(image: Image.Image, font: ImageFont.ImageFont) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    text_width = max(draw.textlength(text, font=font) for _, text in LEGEND_ENTRIES)
    width = int(text_width) + 26
    height = LEGEND_PADDING * 2 + LEGEND_LINE_HEIGHT * len(LEGEND_ENTRIES)
    box = (
        LEGEND_MARGIN,
        LEGEND_MARGIN,
        LEGEND_MARGIN + width,
        LEGEND_MARGIN + height,
    )
    draw.rectangle(box, fill=LEGEND_BACKGROUND, outline="black")

    for index, (color, text) in enumerate(LEGEND_ENTRIES):
        y = LEGEND_MARGIN + LEGEND_PADDING + index * LEGEND_LINE_HEIGHT
        dot = (LEGEND_MARGIN + LEGEND_PADDING, y + 2, LEGEND_MARGIN + LEGEND_PADDING + 8, y + 10)
        draw.ellipse(dot, fill=color)
        draw.text((LEGEND_MARGIN + LEGEND_PADDING + 14, y), text, fill="black", font=font)

    image.alpha_composite(overlay)


def _bbox_outline(bbox: BBox) -> list[tuple[float, float]]:
    return [
        (bbox.min_lon, bbox.min_lat),
        (bbox.max_lon, bbox.min_lat),
        (bbox.max_lon, bbox.max_lat),
        (bbox.min_lon, bbox.max_lat),
        (bbox.min_lon, bbox.min_lat),
    ]
