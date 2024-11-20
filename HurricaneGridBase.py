import itertools
import math
import numpy as np
import pandas as pd
from tropycal import tracks
from tropycal.utils import wind_to_category
from utils.geometry import point_in_bbox, get_storm_direction

class HurricaneGridBase:
    # Takes in the bounds of interest and creates a list of 1x1 lat/lon bounding boxes
    def __init__(self, lat_min, lat_max, lon_min, lon_max, basin="north_atlantic", start_year=2000):
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.lat_offset = 0 - lat_min
        self.lon_offset = 0 - lon_min

        self.major_bbox = [
            [lat_min, lon_min],
            [lat_max, lon_min],
            [lat_max, lon_max],
            [lat_min, lon_max]
        ]

        self.year_range = (start_year, 2023)

        self.lat_intervals = [i for i in range(lat_min, lat_max+1)]
        self.lon_intervals = [i for i in range(lon_min, lon_max+1)]
        self.bbox_combos = list(itertools.product(self.lat_intervals, self.lon_intervals))
        self.bbox_combos.append(("OB"))
        # North, East, Other
        # self.directions = ["N", "E", "O"]
        self.categories = [i for i in range(6)]
        # self.markov_entries = list(itertools.product(self.bbox_combos, self.directions))
        self.markov_entries = list(itertools.product(self.bbox_combos, self.categories))
        self.markov_entries.append("T")
        self.markov_chain_counts = np.zeros((len(self.markov_entries), len(self.markov_entries)))
        self.markov_chain_probabilities = np.zeros((len(self.markov_entries), len(self.markov_entries)))

        self.chain_indices = {}
        self.total_values = {i: 0 for i in self.markov_entries}
        for idx, value in enumerate(self.markov_entries):
            self.chain_indices[value] = idx

        self.basin = tracks.TrackDataset(basin=basin)

        self.analogs = self.basin.analogs_from_shape(self.major_bbox, year_range=self.year_range)

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
    
    # This is one storm at a time
    def get_transitions_from_dataframe(self, df: pd.DataFrame):
        df = df.loc[df["extra_obs"] == 0]
        df = df.reset_index()
        _current = []
        _to = []
        for idx, row in df.iterrows():
            if idx == 0:
                # Do nothing
                continue
            else:
                prev = df.iloc[idx-1]
                if idx < (len(df) - 1):
                    cur = self.get_type(prev, row)
                    if len(_current) > 0:
                        _to.append(cur)
                    _current.append(cur)
                if idx == (len(df) - 1) and len(_current) > 0:
                    _to.append(_current[-1])
        if len(_to) > 0:
            _current.append(_to[-1])
            _to.append("T")
        return _current, _to

    def get_type(self, prev, row):
        prev_lat = prev["lat"]
        prev_lon = prev["lon"]
        lat = math.floor(row["lat"])
        lon = math.floor(row["lon"])
        # direction = get_storm_direction(prev_lat, prev_lon, lat, lon)
        category = wind_to_category(row["vmax"])
        # We are considering tropical storms and depressions to be the same category
        if category == -1:
            category = 0
        if (self.lat_min <= lat and lat <= self.lat_max and self.lon_min <= lon and lon <= self.lon_max):
            location = (lat, lon)
        else:
            location = ("OB")
        # return tuple(((location, direction), category))
        return (location, category)

    def fill_mc(self):
        for analog in self.analogs:
            storm = self.basin.get_storm(analog).to_dataframe()
            current, to = self.get_transitions_from_dataframe(storm)
            if (len(current) != len(to)):
                ValueError("List lengths did not match up")
            else:
                for i in range(len(current)):
                    if i != len(current) - 1:
                        if np.isnan(current[i][1]) or np.isnan(to[i][1]):
                            continue
                    else:
                        if np.isnan(current[i][1]):
                            continue
                    # print(f"{current[i]} to {to[i]}")
                    self.total_values[current[i]] += 1
                    row_index = self.chain_indices[current[i]]
                    col_index = self.chain_indices[to[i]]
                    self.markov_chain_counts[row_index, col_index] += 1
        return
    
    def turn_into_probabilities(self):
        for row_entry in range(len(self.markov_entries)):
            for column_entry in range(len(self.markov_entries)):
                count = self.markov_chain_counts[row_entry,column_entry]
                if count == 0:
                    self.markov_chain_probabilities[row_entry,column_entry] = 0
                else:
                    self.markov_chain_probabilities[row_entry,column_entry] = count / self.total_values[self.markov_entries[row_entry]]
        return
    
    def get_mc_probabilities(self):
        return self.markov_chain_probabilities
    
    def get_state_to_idx(self):
        return self.chain_indices
    
    def get_markov_entries(self):
        return self.markov_entries


    
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
