import itertools
from operator import attrgetter, itemgetter
from typing import List, Tuple
import math
import random
from plot_points import LatLng
import matplotlib.pyplot as plt
import pyclipper


def generate_polygon(ctrX, ctrY, aveRadius, irregularity, spikeyness, num_verts):
    """Start with the centre of the polygon at ctrX, ctrY,
        then creates the polygon by sampling points on a circle around the centre.
        Random noise is added by varying the angular spacing between sequential points,
        and by varying the radial distance of each point from the centre.

        Params
        ctrX, ctrY - coordinates of the "centre" of the polygon
        aveRadius - in px, the average radius of this polygon, this roughly controls how
        large the polygon is, really only useful for order of magnitude.
        irregularity - [0,1] indicating how much variance there is in the angular spacing of vertices. [0,1] will map to [0, 2pi/numberOfVerts]
        spikeyness - [0,1] indicating how much variance there is in each vertex from the circle of radius aveRadius. [0,1] will map to [0, aveRadius]
        numVerts - self-explanatory

        Returns a list of vertices, in CCW order.
        """

    irregularity = clip(irregularity, 0, 1) * 2 * math.pi / num_verts
    spikeyness = clip(spikeyness, 0, 1) * aveRadius

    # generate n angle steps
    angleSteps = []
    lower = (math.tau / num_verts) - irregularity
    upper = (math.tau / num_verts) + irregularity
    s = 0
    for _ in itertools.repeat(None, num_verts):
        tmp = random.uniform(lower, upper)
        angleSteps.append(tmp)
        s = s + tmp

    # normalize the steps so that point 0 and point n+1 are the same
    k = s / math.tau
    for i in range(num_verts):
        angleSteps[i] = angleSteps[i] / k

    # now generate the points
    points = []
    angle = random.uniform(0, 2 * math.pi)
    for i in range(num_verts):
        r_i = clip(random.gauss(aveRadius, spikeyness), 0, 2 * aveRadius)
        x = ctrX + r_i * math.cos(angle)
        y = ctrY + r_i * math.sin(angle)
        points.append((int(x), int(y)))

        angle = angle + angleSteps[i]

    return points


def clip(x, _min, _max):
    if _min > _max:
        return x
    elif x < _min:
        return _min
    elif x > _max:
        return _max
    else:
        return x


def point_in_polygon(vertices: List[LatLng], point: LatLng) -> bool:
    test_lat, test_lng = point
    is_inside = False
    j = len(vertices) - 1
    for i, (cur_lat, cur_lng) in enumerate(vertices):
        if ((cur_lng > test_lng) != (vertices[j].lng > test_lng)) and (
            test_lat < (vertices[j].lat - vertices[i].lat) * (test_lng - cur_lng) / (
                vertices[j].lng - cur_lng) + cur_lat):
            is_inside = not is_inside
        j = i

    return is_inside


plt.style.use("fivethirtyeight")
plt.figure(figsize=(18, 12), dpi=200)


def plot_latlng(points: List[LatLng]):
    xs = list(map(attrgetter("lat"), points))
    ys = list(map(attrgetter("lng"), points))
    plt.plot(xs, ys)
    plt.show()


def plot_coords(points: List[Tuple[float, float]]):
    xs = list(map(itemgetter(0), points))
    ys = list(map(itemgetter(1), points))
    xs.append(xs[0])
    ys.append(ys[0])
    plt.plot(xs, ys)
    plt.show()


def plot(xs, ys):
    plt.plot(xs, ys)
    plt.show()

pyclipper.PyclipperOffset

if __name__ == '__main__':
    polygon = generate_polygon(0, 0, 10, 0.5, 0.5, 10)
    plot_coords(polygon)
