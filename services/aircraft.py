import geopy
import geopy.distance as gp_dis
import requests
from config import air_labs_key


def get_distance_point(lat, lon, distance, direction):
    start = geopy.Point(lat, lon)
    d = gp_dis.GeodesicDistance(kilometers=distance)
    return d.destination(point=start, bearing=direction)


def get_aircraft(lat, lon, distance):

    bbox = list(get_distance_point(lat, lon, distance, 225))[0:2]
    bbox += list(get_distance_point(lat, lon, distance, 45))[0:2]

    params = {
        'api_key': air_labs_key,
        'bbox': ','.join(str(round(coordinate, 2)) for coordinate in bbox)
    }

    method = 'flights'
    api_base = 'http://airlabs.co/api/v9/'
    api_result = requests.get(api_base + method, params)
    api_response = api_result.json()

    return api_response


if __name__ == "__main__":
    print(get_aircraft(lat=67.566042, lon=30.478618, distance=310))


