import time
import os

import matplotlib.pylab as plt
import numpy as np
from mpl_toolkits.basemap import Basemap


plt.switch_backend('agg')


def draw_map(man_coordinates, aircraft_coordinates, bbox, path=os.path.join(os.getcwd())):
    map = Basemap(projection='merc',
                  llcrnrlat=float(bbox[0]),
                  urcrnrlat=float(bbox[2]),
                  llcrnrlon=float(bbox[1]),
                  urcrnrlon=float(bbox[3]),
                  resolution='i')

    x, y = map(aircraft_coordinates[1], aircraft_coordinates[0])
    man_x, man_y = map(man_coordinates[1], man_coordinates[0])

    map.fillcontinents(color='gray', lake_color='aqua')
    map.drawmapboundary(fill_color='aqua')
    map.drawrivers(color='aqua')
    map.drawcountries(color='red')
    map.drawparallels(np.arange(float(bbox[0]),
                                float(bbox[2]), 1.), labels=[1, 0, 0, 0], fontsize=8, fmt='%i')
    map.drawmeridians(np.arange(float(bbox[1]),
                                float(bbox[3]), 3.), labels=[0, 0, 0, 1], fontsize=8, fmt='%i')

    map.scatter(x, y, 10, marker='o', color='blue')
    map.scatter(man_x, man_y, marker='*', color='green')
    plt.title("Location aircrafts", fontsize=15)
    plt.draw()
    image_name = str(time.time()).replace('.', '_') + '.png'
    plt.savefig(os.path.join(path, image_name), dpi=200, bbox_inches='tight')

    return image_name


if __name__ == "__main__":
    man = [59.353767, 25.062021]
    lat = [58.800552, 61.343327, 58.363403, 59.150948, 59.917923, 59.723495, 59.445438, 56.181656, 56.499008, 56.761139,
           56.976242, 59.452789, 60.952377, 59.715454, 58.213348, 55.844948, 57.379078, 56.205276, 56.970383, 59.877213,
           57.077698, 59.316513, 55.791412, 55.639847, 60.722321, 58.364403, 59.900757, 60.576611, 58.752228, 57.947762,
           58.313599, 58.771549, 56.449951, 56.905609, 56.14344, 57.399673, 58.94072, 56.951523, 59.629505, 57.609924,
           58.661964, 59.413273, 59.526306, 58.533691, 59.952072, 60.341988, 58.630821, 56.943256, 59.683647, 59.672974,
           59.965576, 59.583298, 59.664654, 59.29]
    lon = [21.006866, 19.07247, 20.475946, 31.682108, 27.712646, 24.274576, 30.809925, 18.022322, 18.806362, 24.106579,
           19.003086, 19.637421, 25.50997, 22.796265, 17.801661, 17.223043, 24.119331, 23.692766, 18.571358, 22.119551,
           18.819313, 18.978516, 17.235218, 17.366138, 18.933367, 17.8125, 19.982025, 18.554535, 22.876648, 23.940399,
           21.40057, 18.111603, 19.922459, 22.095308, 17.933207, 22.734919, 24.534933, 24.414883, 30.917044, 25.06917,
           33.643158, 30.332779, 32.488495, 32.742184, 29.303741, 25.122593, 17.325439, 23.974382, 17.25507, 18.050995,
           18.20179, 17.801514, 17.985092, 31.24]
    bbox = [56.045382693179, 19.385299300680607, 62.36196138800111, 31.899857777106163]

    print(draw_map(man, [lat, lon], bbox))
