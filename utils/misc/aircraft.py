import datetime

import geopy
import geopy.distance as gp_dis
import requests
from loguru import logger

from config_data import config
from database.database import User, Aircraft


def get_distance_point(lat: float, lon: float, distance: int, direction: int) -> geopy.Point:
    """
    Функция для определения точки по известным данным (известная точка, расстояние, угол)

    :argument:
        lat (float): широта известной точки
        lon (float): долгота известной точки
        distance (int): удаление от известной точки
        direction (int): азимут удаление от известной точки

    :return:
        (geopy.Point): широта и долгота точки

    """
    start = geopy.Point(lat, lon)
    d = gp_dis.GeodesicDistance(kilometers=distance)
    return d.destination(point=start, bearing=direction)


def get_aircraft(user: User, distance: int) -> None:
    """
    Функция для получения данных о воздушных судах с сайта http://airlabs.co/
    и записи этих данных в БД

    :argument:
        user (User): объект пользователя
        distance (int): удаление от известной точки

    """
    lat, lon = user.location.split(", ")

    bbox = list(get_distance_point(float(lat), float(lon), distance, 225))[0:2]
    bbox += list(get_distance_point(float(lat), float(lon), distance, 45))[0:2]

    user.bbox = "{}, {}, {}, {}".format(bbox[0], bbox[1], bbox[2], bbox[3])
    user.last_req = datetime.datetime.now()
    user.save()

    params = {
        "api_key": config.AIR_LABS_API_KEY,
        "bbox": ",".join(str(round(coordinate, 2)) for coordinate in bbox)
    }

    method = "flights"
    api_base = "http://airlabs.co/api/v9/"
    api_result = requests.get(api_base + method, params)
    api_response = api_result.json()
    if api_result.status_code == 200 and 'error' not in api_response:
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
    else:
        if 'error' in api_response:
            logger.error(f"{api_response['error']['message']}")
        else:
            logger.error("Ресурс http://airlabs.co/ недоступен.")

