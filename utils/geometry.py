from geographiclib.geodesic import Geodesic
import shapely

# bbox is a list of tuples and point is a tuple
def point_in_bbox(bbox: list, point: tuple):
    pt = shapely.Point(point)
    shapely_box = shapely.Polygon(bbox)
    return shapely_box.contains(pt)
