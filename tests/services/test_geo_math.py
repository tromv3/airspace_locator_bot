import pytest

from bot.services.geo_math import bbox_from_point


def test_bbox_is_centered_on_origin():
    bbox = bbox_from_point(55.7558, 37.6173, 100)

    assert bbox.min_lat < 55.7558 < bbox.max_lat
    assert bbox.min_lon < 37.6173 < bbox.max_lon


def test_bbox_grows_with_distance():
    small = bbox_from_point(55.7558, 37.6173, 100)
    large = bbox_from_point(55.7558, 37.6173, 300)

    assert large.max_lat - large.min_lat > small.max_lat - small.min_lat
    assert large.max_lon - large.min_lon > small.max_lon - small.min_lon


@pytest.mark.parametrize(
    ("lat", "lon"),
    [(0.0, 0.0), (-33.87, 151.21), (55.7558, 37.6173)],
)
def test_bbox_corners_are_ordered(lat, lon):
    bbox = bbox_from_point(lat, lon, 150)

    assert bbox.min_lat < bbox.max_lat
    assert bbox.min_lon < bbox.max_lon
