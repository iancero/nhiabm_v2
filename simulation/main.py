import os, json
import random
import multiprocessing as mp
import time

from simulation import Simulation


def run_simulation(params):
    random.seed(params["seed"])

    sim = Simulation(**params)
    sim.setup()
    sim.go()

    result_path = f"experiments/mock_experiment/sim_results_{params['seed']}.json"
    with open(result_path, "w") as f:
        f.write(json.dumps(sim.history))

    return result_path


def main():
    experiment_dir = "experiments/mock_experiment/"
    param_file = os.path.join(experiment_dir, "input_parameter_combinations.json")
    with open(param_file, "r") as f:
        param_combos = json.load(f)

    with mp.Pool(processes=mp.cpu_count()) as pool:
        results = pool.map_async(run_simulation, param_combos)

        # close the process pool
        pool.close()

        # wait for all tasks to complete
        pool.join()

    return results


if __name__ == "__main__":

    # Note: took about 2.5 hours for 20,000 samples

    print("Start", time.ctime())

    main()

    print("Done", time.ctime())
