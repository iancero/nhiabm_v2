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


def main():
    print(time.ctime())

    with mp.Pool(processes=8) as pool:
        db = Database("experiments/mock_experiment/test.db")

        for result in pool.imap_unordered(run_simulation, range(104)):

            # TODO: for speed, possibly implement a stable SQLITE connection,
            # the __exit__ method of SQLite seems to be taking a long time,
            # from the performance profile count, it looks like sqlite is getting
            # opened and closed each time there is an "insert_all" call from sqlite-utils
            # its unclear, but possible.

            for aspect, content in result.items():
                db[aspect].insert_all(content)

        db.close()

    print(time.ctime())


if __name__ == "__main__":
    main()
