from geographiclib.geodesic import Geodesic
import shapely

# bbox is a list of tuples and point is a tuple
def point_in_bbox(bbox: list, point: tuple):
    pt = shapely.Point(point)
    shapely_box = shapely.Polygon(bbox)
    return shapely_box.contains(pt)

def getStormDirection(prev_lat, prev_lon, lat, lon):
    
    import numpy as np

    # find differences between previous and current lats and lons
    lat_diff = lat - prev_lat
    lon_diff = lon - prev_lon
    
    # error conditions for arctan: denominator (lon_diff) is zero; then we'll only consider lat
    
    if lon_diff == 0:
        
        if not lat_diff == 0:
            
            if lat_diff > 0: # positive, traveling north
                stormDir = "N"
                
            else: # negative, traveling south
                stormDir = "O" # south defined as other
                
        else: # if (lon_diff == 0 and lat_diff == 0)
            stormDir = "O" # direction defined as other for stationary
            
    elif lat_diff == 0: # we can't trust that arctan will properly interpret west vs east 
        
        if lon_diff > 0: # if moved east
            stormDir = "E"
        else: # if moved west
            stormDir = "O" 
            
    else: # if lon_diff and lat_diff are nonzero
            
        stormAngle = np.arctan2(lat_diff, lon_diff)
            
        # define direction given storm angle
        if (stormAngle > (np.pi/4) and stormAngle <= ((3*np.pi)/4)):
            stormDir = "N" # north defined as a pi/2 segment of the unit circle bisected by "true north"
        elif (abs(stormAngle) <= (np.pi/4) and abs(stormAngle) >= 0): # absolute values bc it was getting confused by small negative angles
            stormDir = "E" # east defined as pi/2 segment of unit circle bisected by "true east"
        else:
            stormDir = "O"
        
    return stormDir
        
        
