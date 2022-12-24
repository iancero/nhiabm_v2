from itertools import repeat
import random

from sqlite_utils import Database
from parameter_sampling import sample_parameter_space
from simulation import Simulation
import multiprocessing as mp

import time


def run_simulation(sim_id):

    print(f"starting {sim_id}")

    param_file = "experiments/mock_experiment/mock_input_params.json"
    params = sample_parameter_space(param_file, n_samples=1)[0]
    params.update({"sim_id": sim_id})

    sim = Simulation(**params)
    sim.setup()
    sim.go()

    print(f"returning {sim_id}")

    return sim.history_for_db()


if __name__ == "__main__":

    print(time.ctime())

    with mp.Pool(processes=8) as pool:
        db = Database("experiments/mock_experiment/test.db")

        for result in pool.imap_unordered(run_simulation, range(8)):

            for aspect, content in result.items():
                db[aspect].insert_all(content)

        db.close()

    print(time.ctime())
