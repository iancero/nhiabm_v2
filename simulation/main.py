import sqlite3
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

    return sim


def simulation_to_db(queue, db_path):
    with sqlite3.connect(db_path) as con:

        # initialize database tables
        example_sim = run_simulation(sim_id=-1)
        example_sim.create_history_tables(con)
        print("DB tables created (or detected)")

    while True:
        completed_sim = queue.get()

        if completed_sim is None:
            break

        completed_sim.insert_history_to_db(con)

        print("\tdb entry completed", completed_sim.sim_id)


def main():
    print(time.ctime())

    n_simulations = 1000

    # initialize database entry queue and process
    db_path = "test_1000.db"
    queue = mp.Queue()
    db_process = mp.Process(target=simulation_to_db, args=(queue, db_path))
    db_process.start()

    # run simulations and enter to DB asynchronously
    with mp.Pool(processes=7) as pool:
        for completed_sim in pool.imap_unordered(run_simulation, range(n_simulations)):
            queue.put(completed_sim)

    # finalize and close database entry queue and process
    queue.put(None)

    db_process.join()
    db_process.close()

    queue.close()

    print(time.ctime())


if __name__ == "__main__":
    main()
