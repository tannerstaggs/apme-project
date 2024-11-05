import itertools
import math
import numpy as np
from tropycal import tracks
from utils.geometry import point_in_bbox

class HurricaneGridBase:
    # Takes in the bounds of interest and creates a list of 1x1 lat/lon bounding boxes
    def __init__(self, lat_min, lat_max, lon_min, lon_max, basin="north_atlantic"):
        self.lat_offset = 0 - lat_min
        self.lon_offset = 0 - lon_min

        self.lat_intervals = [i for i in range(lat_min, lat_max+1)]
        self.lon_intervals = [i for i in range(lon_min, lon_max+1)]
        self.bbox_combos = list(itertools.product(self.lat_intervals, self.lon_intervals))
        # North, East, Other
        self.directions = ["N", "E", "O"]
        self.markov_entries = list(itertools.product(self.bbox_combos, self.directions))
        self.markov_chain = np.zeros((len(self.markov_entries), len(self.markov_entries)))

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
    
    def create_bbox_from_entry(self, entry: str):
        lat_lon_tuple = entry[0]
        lat = lat_lon_tuple[0]
        lon = lat_lon_tuple[1]
        return [
            [lat, lon],
            [lat+1, lon],
            [lat+1, lon+1],
            [lat, lon+1]
        ]
    
    # Note: I think we don't need this now that we have changed the markov chain
    # Finds the entry that a lat, lon point should correspond to
    # def get_entry_for_lat_lon(self, lat, lon):
    #     lat = lat + self.lat_offset
    #     lon = lon + self.lon_offset

    #     if (lat < 0 or lat > len(self.lat_intervals) or lon < 0 or lon > len(self.lon_intervals)):
    #         raise ValueError("Value(s) outside of proper bounds")

    #     lat_idx = math.floor(lat / (len(self.lon_intervals)))
    #     lon_idx = math.floor(lon % len(self.lon_intervals))
    #     return lat_idx, lon_idx
    
    # I also think we don't need this now
    # # I think this works but I need to be convinced
    # def from_indices_to_bbox_idx(self, lat_idx, lon_idx):
    #     pos = lat_idx * len(self.lon_intervals)
    #     pos += lon_idx
    #     return pos
    
    # Transition matrix is not the transition probability matrix, it just counts transitions from i to j
    # This one is not tested yet
    # def get_occurence_i_to_j(self, i_lat_idx, i_lon_idx, j_lat_idx, j_lon_idx):
    #     i_to_j_count = 0
    #     i_bbox_idx = self.from_indices_to_bbox_idx(i_lat_idx, i_lon_idx)
    #     j_bbox_idx = self.from_indices_to_bbox_idx(j_lat_idx, j_lon_idx)
    #     for storm in self.basin.analogs_from_shape(self.bboxes[i_bbox_idx]):
    #         storm_df = self.basin.get_storm(storm).to_dataframe()
    #         storm_df.sort_values(by="time", inplace=True)
    #         for idx, row in storm_df.iterrows():
    #             next_row = storm_df.iloc[idx+1]
    #             next_lat = float(next_row["lat"])
    #             next_lon = float(next_row["lon"])
    #             next_entry = self.get_entry_for_lat_lon(next_lat, next_lon)
    #             if next_entry == j_bbox_idx:
    #                 i_to_j_count += 1
    #     return i_to_j_count
