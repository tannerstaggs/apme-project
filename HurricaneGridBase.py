import math
from tropycal import tracks
from utils.geometry import point_in_bbox

class HurricaneGridBase:
    # Takes in the bounds of interest and creates a list of 1x1 lat/lon bounding boxes
    def __init__(self, lat_min, lat_max, lon_min, lon_max, basin="north_atlantic"):
        self.lat_offset = 0 - lat_min
        self.lon_offset = 0 - lon_min

        self.lat_intervals = [i for i in range(lat_min, lat_max+1)]
        self.lon_intervals = [i for i in range(lon_min, lon_max+1)]
        self.bboxes = []
        for i in range(0, len(self.lat_intervals)-1):
            for j in range(0, len(self.lon_intervals)-1):
                bbox = [(self.lat_intervals[i], self.lon_intervals[j]), 
                        (self.lat_intervals[i+1], self.lon_intervals[j]),
                        (self.lat_intervals[i+1], self.lon_intervals[j+1]),
                        (self.lat_intervals[i], self.lon_intervals[j+1])]
                self.bboxes.append(bbox)

        self.basin = tracks.TrackDataset(basin=basin)

    # Counts observations from dataset in a particular bounding box
    def observations_in_bbox(self, bbox):
        num_observations = 0
        for storm in self.basin.analogs_from_shape(bbox):
            storm_df = self.basin.get_storm(storm).to_dataframe()
            for df_idx, row in storm_df.iterrows():
                if point_in_bbox(bbox, (row["lat"], row["lon"])):
                    num_observations += 1
        return num_observations
    
    # Finds the entry that a lat, lon point should correspond to
    def get_entry_for_lat_lon(self, lat, lon):
        lat = lat + self.lat_offset
        lon = lon + self.lon_offset

        if (lat < 0 or lat > len(self.lat_intervals) or lon < 0 or lon > len(self.lon_intervals)):
            raise ValueError("Value(s) outside of proper bounds")

        lat_idx = math.floor(lat / (len(self.lon_intervals)))
        lon_idx = math.floor(lon % len(self.lon_intervals))
        return lat_idx, lon_idx