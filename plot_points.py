from dataclasses import dataclass, astuple
from typing import List
import time
from itertools import islice, cycle
import pickle
import numpy as np
from hexcode import encode, shorten
from bokeh.plotting import figure, output_notebook, show
from bokeh.palettes import Dark2_5

take = lambda iterable, num: tuple(islice(iterable, 0, num))

NOT_FOUND = -1


@dataclass(frozen=True)
class LatLng:
    lat: float
    lng: float

    def __iter__(self):
        yield from astuple(self)


@dataclass(frozen=True)
class BoundingBox:
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float

    def __iter__(self):
        yield from astuple(self)

    @staticmethod
    def from_polygon(polygon: List):

        bounding_box = None

        for data in polygon:
            if data['geojson']['type'] == 'Polygon':
                bounding_box = data['boundingbox']

        if bounding_box is None:
            return BoundingBox(float('-inf'), float('inf'), float('-inf'), float('inf'))

        else:
            return BoundingBox(*map(float, bounding_box))


@dataclass(frozen=True)
class Polygon:
    place_id: int
    reference_point: LatLng
    bounding_box: List[LatLng]
    display_name: str
    coordinates: List[LatLng]

    @staticmethod
    def from_polygon(polygon: List):
        # get coordinates
        coordinates_list = extract_xy_from_polygon_object(polygon)
        coords_latlng = list(map(lambda x: LatLng(x[1].item(), x[0].item()), coordinates_list))

        # get the bounds
        array_bounds = get_bounds(polygon)

        bounding_box = []
        for i, j in zip(array_bounds[0], array_bounds[1]):
            bounding_box.append(LatLng(i, j))

        # get the placeID
        place_id = get_place_id(polygon)

        # get the display_name
        display_name = get_display_name(polygon)

        # get the reference point
        reference_point = get_reference_point(polygon)

        return Polygon(place_id, reference_point, bounding_box, display_name, coords_latlng)


def extract_xy_from_polygon_object(polygon):
    for data in polygon:
        geo_json = data['geojson']

        if geo_json['type'] == 'Polygon':
            return np.array(geo_json['coordinates'][0])
    else:
        return None


def get_bounds(polygon):
    for data in polygon:
        if data['geojson']['type'] == 'Polygon':
            bounding_box = data['boundingbox']
            xs = [bounding_box[0], bounding_box[1], bounding_box[1], bounding_box[0], bounding_box[0]]
            ys = [bounding_box[2], bounding_box[2], bounding_box[3], bounding_box[3], bounding_box[2]]
            return np.array([list(map(float, xs)), list(map(float, ys))])

    else:
        return None


def get_place_id(polygon):
    for data in polygon:
        if data['geojson']['type'] == 'Polygon':
            return data['place_id']

    else:
        return None


def get_reference_point(polygon):
    for data in polygon:
        if data['geojson']['type'] == 'Polygon':
            return LatLng(float(data['lat']), float(data['lon']))

    else:
        return None


def get_display_name(polygon):
    for data in polygon:
        if data['geojson']['type'] == 'Polygon':
            name = data['display_name'].split(',')[0]

            if 'Province' in name:
                end_index = name.index(' Province')
                return name[:end_index]

            return name

    else:
        return None


def plot_polygons(polygons):
    output_notebook()
    plot = figure(plot_height=1080, plot_width=1920, hidpi=True)
    colors = cycle(Dark2_5)
    for polygon in polygons:
        coords = extract_xy_from_polygon_object(polygon)

        if coords is None:
            continue

        try:
            bounds = get_bounds(polygon)

        except IndexError:
            continue

        plot.line(x=coords[:, 0], y=coords[:, 1], color='gray')
        plot.line(bounds[1], bounds[0], color=next(colors))
    show(plot)


bb_memo = None
bb_to_polygon = None
json_objects = []


def unpickle_json_objects():
    global json_objects
    with open("json_objects_list.pickle", 'rb') as f0:
        file_ = pickle.load(f0)

        for json_object in file_:
            polygon = Polygon.from_polygon(json_object)
            json_objects.append(polygon)


def unpickle_bb_memo():
    global bb_memo
    with open("sorted_bbs.pickle", 'rb') as f0:
        bb_memo = pickle.load(f0)


def unpickle_bb_to_polygon():
    global bb_to_polygon
    with open("bb_to_polygon.pickle", 'rb') as f0:
        bb_to_polygon = pickle.load(f0)


def candidate_polygons(json_objects: List[Polygon], point: LatLng):
    polygons = []
    for polygon in json_objects:
        if point_in_polygon(polygon.bounding_box, point):
            if point_in_polygon(polygon.coordinates, point):
                polygons.append(polygon)
                return polygons

    return None


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


if __name__ == '__main__':
    start = time.time()
    unpickle_bb_memo()
    unpickle_bb_to_polygon()
    unpickle_json_objects()
    print('Unpickling time: ', time.time() - start)

    print('\n')

    points = [LatLng(-20.015061, 28.620266), LatLng(-17.913307, 30.973464), LatLng(-20.483428, 29.917561), LatLng(-15.890460, 29.380621), LatLng(-19.550485, 29.731946)]
    count = 1
    for point in points:
        start = time.time()
        hexcode_ = encode(point.lat, point.lng)

        bounding_boxes = candidate_polygons(json_objects, point)
        if bounding_boxes is None:
            print(None)
            print()
            continue

        for bb in bounding_boxes:
            short_code = shorten(hexcode_, bb.reference_point.lat, bb.reference_point.lng)
            print('Point {}:'.format(count))
            print('{}.{}'.format(bb.display_name, short_code))
            print(time.time() - start)
            count += 1
            print()
