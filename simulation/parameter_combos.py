from itertools import product, repeat
import json


def parameter_combinations(param_dict, runs_per_combo, nonvarying_names=None):

    if nonvarying_names is not None:
        # hold things that should stay lists to the side
        nonvarying_lists = {key: param_dict.pop(key) for key in nonvarying_names}

    param_combos = []
    for param_combo in product(*param_dict.values()):
        param_combo = dict(zip(param_dict, param_combo))

        # re-insert nonvarying hold out lists from above
        if nonvarying_names:
            param_combo.update(nonvarying_lists)

        # repeat for as many samples as desires
        param_iterations = list(repeat(param_combo, times=runs_per_combo))

        param_combos.append(param_iterations)

    return param_combos


if __name__ == "__main__":

    with open("input_params.json", "r") as f:
        params = json.load(f)

    # Get combos of intervention parameters first, then put combos back in params object
    intervention_params = params.pop("intervention_params")
    intervention_combos = parameter_combinations(intervention_params, runs_per_combo=1)
    params.update({"intervention_params": intervention_combos})

    # Create all combinations of parameters and interventions
    param_combos = parameter_combinations(
        param_dict=params, runs_per_combo=1, nonvarying_names=["baserates", "sui_ORs"]
    )

    with open("experiments/input_parameter_combinations.json", "w") as f:
        f.write(json.dumps(param_combos))
