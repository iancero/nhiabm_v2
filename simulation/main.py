import os, json

from simulation import Simulation

if __name__ == "__main__":

    experiment_dir = "experiments/practice_exp_1/"
    param_dir = os.path.join(experiment_dir, "params")
    result_dir = os.path.join(experiment_dir, "results")

    param_files = [f for f in os.listdir(param_dir) if f.endswith(".json")]
    result_files = [f"results_{param_file}" for param_file in param_files]

    for param_file, result_file in zip(param_files, result_files):

        # Read in parameter information
        param_path = os.path.join(param_dir, param_file)
        with open(param_path, "r") as f:
            params = json.load(f)

        # Run simulation from start to finish
        sim = Simulation(**params)
        sim.setup()
        sim.go()

        # Write simulation history to output json file
        result_path = os.path.join(result_dir, result_file)
        with open(result_path, "w") as f:
            json.dumps(sim.history)
