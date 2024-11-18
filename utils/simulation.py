import numpy as np

def monteCarloPathPredict(probs):
    rng = np.random.default_rng() # initialize Generator
    return rng.choice(np.array(range(len(probs))), p=probs) # will output index of selection in row

