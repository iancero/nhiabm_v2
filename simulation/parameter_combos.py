import copy
from itertools import product, repeat
import json
import random


def param_combinations(param_dict, runs_per_combo, number_iterations=False):

    # (1) create intervention combinations first
    if "intervention_params" in param_dict:
        intervention_params = []
        for intv in param_dict["intervention_params"]:
            intv_combos = param_combinations(intv, runs_per_combo=1)
            intervention_params.extend([[intv_combo] for intv_combo in intv_combos])

        param_dict.update({"intervention_params": intervention_params})

    # (2) construct all combinations of parameters in param_dict
    param_combos = []
    for param_combo in product(*param_dict.values()):

        param_combo = dict(zip(param_dict, param_combo))

        # repeat for as many samples as desired
        param_iterations = []
        for i, combo in enumerate(repeat(param_combo, times=runs_per_combo)):
            param_iteration = copy.deepcopy(combo)

            if number_iterations:
                param_iteration.update({"sample_num": i})

            param_iterations.append(param_iteration)

        param_combos.extend(param_iterations)

    return param_combos


if __name__ == "__main__":

    with open("input_params.json", "r") as f:
        params = json.load(f)

    param_combos = param_combinations(
        param_dict=params, runs_per_combo=100, number_iterations=True
    )

    for param_combo in param_combos:
        param_combo.update({"seed": random.randint(a=1e6, b=1e7)})

    with open(
        "experiments/mock_experiment/input_parameter_combinations.json", "w"
    ) as f:
        f.write(json.dumps(param_combos))
