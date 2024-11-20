import datetime
import pickle as pkl
import pandas as pd
import numpy as np
from utils.simulation import monteCarloPathPredict
from HurricaneGridBase import HurricaneGridBase
import uuid
import random

class HurricaneSim:
    def __init__(self, data_dir, hgb, initial_state, lead_time):
        self.data_dir = data_dir
        hgb.fill_mc()
        hgb.turn_into_probabilities()
        self.mc = hgb.get_mc_probabilities()
        self.state_to_idx = hgb.get_state_to_idx()
        self.idx_to_state = hgb.get_markov_entries()
        self.sim = pd.DataFrame({"LeadTime": [], "SimNum": [], "TimeStep": [], "Lat": [], "Lon": [], "Direction": [], "Category": []})
        # self.initial_state = initial_state
        # if initial_state == "T":
        #     ValueError("Cannot start with terminated state")
        # self.pos_and_direction = initial_state[0]
        # self.init_position = self.pos_and_direction[0]
        # if self.init_position == "OB":
        #     ValueError("Cannot start with out of bounds storm")
        # self.init_direction = self.pos_and_direction[1]
        # self.init_category = initial_state[1]
        self.lead_time = lead_time
        self.category_to_type = {0: "TS", 1: "H", 2: "H", 3: "H", 4: "H", 5: "H"}
        self.category_to_vmax = {-1: 33, 0: 34, 1: 64, 2: 83, 3: 96, 4: 113, 5: 137}

    def make_step(self, state):
        idx = self.state_to_idx[state]
        # pos, direction, category = self.parse_state(state)
        pos, category = self.parse_state(state)
        if pos != "OB":
            lat = pos[0]
            lon = pos[1]
        row = self.mc[idx]
        # if np.sum(row) != 1:
        #     if direction == "N":
        #         lat = lat + 1
        #     elif direction == "E":
        #         lon = lon + 1
        #     else:
        #         num = random.randint(0, 1)
        #         if num:
        #             direction == "E"
        #         else: 
        #             direction == "N"
            # state = (((lat, lon), direction), category)
            # state = ((lat, lon), category)
            # idx = self.state_to_idx[state]
            # return idx
        print(np.unique(row, return_counts=True))
        return monteCarloPathPredict(row)
    
    def run_sim(self, max_steps, sim_num):
        df = pd.DataFrame({
                            "name": [], 
                            "id": [],
                            "source": [],
                            "time": [],
                            "lat": [],
                            "lon": [],
                            "vmax": [],
                            "type": [],
                            "mslp": [],
                            "wmo_basin": [],
                            "ace": [],
                            "leadtime": [],
                            "sim_num": []
                           })
        name = "milton"
        id = self.return_uuid()
        source = "hurdat"
        start_time = self.lead_time
        state = self.initial_state
        state_idx = self.state_to_idx[state]
        states = []
        i = 0
        while state != "T" and i < max_steps:
            added_hours = (i * 6)
            time = start_time + datetime.timedelta(hours=added_hours)
            pos, category = self.parse_state(state)
            if pos == "OB":
                break
            # pos, direction, category = self.parse_state(state)
            lat, lon = pos[0] + 0.5, pos[1] + 0.5
            type = self.category_to_type[category]
            vmax = self.category_to_vmax[category]
            mslp = 0
            wmo_basin = "north_atlantic"
            ace = 0
            row = pd.DataFrame({
                            "name": [name], 
                            "id": [id],
                            "source": [source],
                            "time": [time],
                            "lat": [lat],
                            "lon": [lon],
                            "vmax": [vmax],
                            "type": [type],
                            "mslp": [mslp],
                            "wmo_basin": [wmo_basin],
                            "ace": [ace],
                            "leadtime": [self.lead_time],
                            "sim_num": [sim_num]
                           })
            df = pd.concat([df, row], ignore_index=True)
            states.append(state)
            state_idx = self.make_step(state)
            state = self.idx_to_state[state_idx]
            i += 1
        if state == "T":
            states.append(state)
        return df
    
    def repeat_simulations(self, num_sims):
        df = pd.DataFrame({
                        "name": [], 
                        "id": [],
                        "source": [],
                        "time": [],
                        "lat": [],
                        "lon": [],
                        "vmax": [],
                        "type": [],
                        "mslp": [],
                        "wmo_basin": [],
                        "ace": [],
                        "leadtime": [],
                        "sim_num": []
                        })
        for i in range(num_sims):
            new_df = self.run_sim(max_steps=16, sim_num=i)
            df = pd.concat([df, new_df], ignore_index=True)
        return df
    
    def sim_lead_times(self, lead_times, states, num_sims):
        df = pd.DataFrame({
                    "name": [], 
                    "id": [],
                    "source": [],
                    "time": [],
                    "lat": [],
                    "lon": [],
                    "vmax": [],
                    "type": [],
                    "mslp": [],
                    "wmo_basin": [],
                    "ace": [],
                    "leadtime": [],
                    "sim_num": []
                    })
        list_len = len(lead_times)
        if list_len != len(states):
            ValueError("List length mismatch")
        else:
            for i in range(list_len):
                lead_time = lead_times[i]
                state = states[i]
                self.set_lead_time(lead_time)
                self.set_init_state(state)
                new_df = self.repeat_simulations(num_sims)
                df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(self.data_dir+"/sims.csv")


     
    def return_uuid(self):
        return uuid.uuid4()
    
    def parse_state(self, state):
        position, category = state[0], state[1]
        return position, category
        # position, direction = _[0], _[1]
        # return position, direction, category
    
    def set_lead_time(self, lead_time):
        self.lead_time = lead_time

    def set_init_state(self, state):
        self.initial_state = state
        if state == "T":
            ValueError("Cannot start with terminated state")
        # self.pos_and_direction = state[0]
        # self.init_position = self.pos_and_direction[0]
        self.init_position = state[0]
        if self.init_position == "OB":
            ValueError("Cannot start with out of bounds storm")
        # self.init_direction = self.pos_and_direction[1]
        self.init_category = state[1]



if __name__ == "__main__":
    hgb = HurricaneGridBase(15, 40, -100, -65, start_year=1930)
    hsim = HurricaneSim("sim_data", hgb, None, None)
    lead_times = [datetime.datetime(2024, 10, 6, 23), datetime.datetime(2024, 10, 7, 5)]
    states = [((22, -94), 1), ((22, -93), 2)]
    hsim.sim_lead_times(lead_times, states, num_sims=10)
