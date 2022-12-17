import os, json
import random
import multiprocessing as mp
import time

from parameter_sampling import sample_parameter_space
from simulation import Simulation


def run_simulation(params):
    random.seed(params["seed"])

    sim = Simulation(**params)
    sim.setup()
    sim.go()

    result_path = f"experiments/mock_experiment/sim_results_{params['sample_num']}.json"
    with open(result_path, "w") as f:
        f.write(json.dumps(sim.history))

    return result_path


def main():
    experiment_dir = "experiments/mock_experiment/"

    input_param_file = os.path.join(experiment_dir, "mock_input_params.json")
    sample_parameters = sample_parameter_space(input_param_file, n_samples=1000)

    for i, samp in enumerate(sample_parameters):
        x = run_simulation(samp)
        print(x)

    with mp.Pool(processes=mp.cpu_count()) as pool:
        results = pool.map_async(run_simulation, sample_parameters, chunksize=50)
        pool.close()
        pool.join()

    return results


if __name__ == "__main__":

    # note: took about 2.5 hours for 20,000 samples

    print("Start", time.ctime())

    main()

    print("Done", time.ctime())
