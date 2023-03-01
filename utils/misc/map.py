import time
import os

from loguru import logger
import matplotlib.pylab as plt
import numpy as np
from mpl_toolkits.basemap import Basemap


plt.switch_backend("agg")


def draw_map(man_coordinates: list,
             aircraft_coordinates: list,
             area: list,
             path: str = os.path.join(os.getcwd())) -> str:

    schema = Basemap(projection="merc",
                     llcrnrlat=float(area[0]),
                     urcrnrlat=float(area[2]),
                     llcrnrlon=float(area[1]),
                     urcrnrlon=float(area[3]),
                     resolution="i")
    """
    Функция для отрисовки воздушных судов на карте

    :argument:
        man_coordinates (list): координаты пользователя
        aircraft_coordinates (list): координаты воздушных судов
        area (list): координаты области
        path (str): путь к папке со временными файлам (temp)

    :return:
        (str): наименование файла(рисунка)

    """
    x, y = schema(aircraft_coordinates[1], aircraft_coordinates[0])
    man_x, man_y = schema(man_coordinates[1], man_coordinates[0])

    schema.fillcontinents(color="gray", lake_color="aqua")
    schema.drawmapboundary(fill_color="aqua")
    schema.drawrivers(color="aqua")
    schema.drawcountries(color="red")
    schema.drawparallels(np.arange(float(area[0]),
                                   float(area[2]), 1.), labels=[1, 0, 0, 0], fontsize=8, fmt="%i")
    schema.drawmeridians(np.arange(float(area[1]),
                                   float(area[3]), 3.), labels=[0, 0, 0, 1], fontsize=8, fmt="%i")

    schema.scatter(x, y, 10, marker="o", color="blue")
    schema.scatter(man_x, man_y, marker="*", color="green")
    plt.title("Location aircraft", fontsize=15)
    plt.draw()
    image_name = str(time.time()).replace(".", "_") + ".png"
    plt.savefig(os.path.join(path, image_name), dpi=200, bbox_inches="tight")
    plt.clf()

    return image_name

# TODO: Добавить легенду карты
