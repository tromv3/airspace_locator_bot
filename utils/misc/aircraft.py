import datetime

import geopy
import geopy.distance as gp_dis
import requests

from config_data import config
from database.database import User, Aircraft


def get_distance_point(lat, lon, distance, direction):
    start = geopy.Point(lat, lon)
    d = gp_dis.GeodesicDistance(kilometers=distance)
    return d.destination(point=start, bearing=direction)


def get_aircraft(user: User, distance: int):
    lat, lon = user.location.split(',')

    bbox = list(get_distance_point(float(lat), float(lon), distance, 225))[0:2]
    bbox += list(get_distance_point(float(lat), float(lon), distance, 45))[0:2]

    user.bbox = '{}, {}, {}, {}'.format(bbox[0], bbox[1], bbox[2], bbox[3])
    user.last_req = datetime.datetime.now()
    user.save()

    params = {
        'api_key': config.AIR_LABS_API_KEY,
        'bbox': ','.join(str(round(coordinate, 2)) for coordinate in bbox)
    }

    method = 'flights'
    api_base = 'http://airlabs.co/api/v9/'
    api_result = requests.get(api_base + method, params)
    api_response = api_result.json()

    Aircraft.delete().where(Aircraft.user == user.id).execute()

    aircraft = list(api_response['response'])
    for air in aircraft:
        plane = Aircraft.create(user=user.id,
                                reg_number=air['reg_number'] if 'reg_number' in air else None,
                                flag=air['flag'] if 'flag' in air else None,
                                type_plane=air['aircraft_icao'] if 'aircraft_icao' in air else None,
                                latitude=air['lat'] if 'lat' in air else None,
                                longitude=air['lng'] if 'lng' in air else None,
                                alt=air['alt'] if 'alt' in air else None)
        plane.save()

