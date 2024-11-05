from geographiclib.geodesic import Geodesic
import shapely

# bbox is a list of tuples and point is a tuple
def point_in_bbox(bbox: list, point: tuple):
    pt = shapely.Point(point)
    shapely_box = shapely.Polygon(bbox)
    return shapely_box.contains(pt)

# Return a "N" "E" or "O" based on bearing
def get_direction(lat1: float, lon1: float, lat2: float, lon2: float):
    result = Geodesic.Inverse(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2)
    bearing = result["azi1"]

    if bearing > 45 and bearing <= 135:
        return "E"
    elif bearing > 135 and bearing < 315:
        return "O"
    else:
        return "N"