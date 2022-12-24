import numpy
import json
from itertools import repeat


def random_values(string):
    random_values = eval(string)

    if isinstance(random_values, numpy.ndarray):
        random_values = numpy.ndarray.tolist(random_values)

    return random_values


def random_parameters(input_params):

    randomized_params = input_params.copy()
    for key, val in randomized_params.items():

        # choose an intervention and randomize intervention parameters
        if key == "intervention_params":
            selected_intervention = numpy.random.choice(randomized_params[key])
            randomized_params[key] = [random_parameters(selected_intervention)]

        # randomize any top-level intervention parameters
        if isinstance(val, str) and "numpy.random" in val:
            randomized_params[key] = random_values(val)

    return randomized_params


def sample_parameter_space(input_json, n_samples):
    with open(input_json, "r") as f:
        input_params = json.load(f)

    exp_conditions = [random_parameters(p) for p in repeat(input_params, n_samples)]

    for i, condition in enumerate(exp_conditions):
        seed = round(numpy.random.default_rng().uniform(low=1e6, high=1e7))
        condition.update({"sample_num": i, "seed": seed})

    return exp_conditions
