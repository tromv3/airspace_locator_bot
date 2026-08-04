from dataclasses import dataclass

import geopy.distance
from geopy import Point

# Corner points relative to the origin, chosen so a single distance produces
# a square-ish bbox: 225° (SW) gives the min corner, 45° (NE) gives the max corner.
_SOUTHWEST_BEARING = 225
_NORTHEAST_BEARING = 45


@dataclass(frozen=True)
class BBox:
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


def bbox_from_point(lat: float, lon: float, distance_km: float) -> BBox:
    origin = Point(lat, lon)
    distance = geopy.distance.geodesic(kilometers=distance_km)
    sw = distance.destination(point=origin, bearing=_SOUTHWEST_BEARING)
    ne = distance.destination(point=origin, bearing=_NORTHEAST_BEARING)
    return BBox(
        min_lat=sw.latitude, min_lon=sw.longitude, max_lat=ne.latitude, max_lon=ne.longitude
    )
