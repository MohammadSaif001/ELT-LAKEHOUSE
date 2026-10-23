import itertools
import json
import random
from typing import Any
from bisect import bisect_right
from src.elt_lakehouse.spark.common.paths import PROFILING_DIR

_DISTRIBUTION_PARAMS_CACHE: dict[int, tuple[list, list]] = {}


def load_distribution(file_name: str) -> dict:
    file_path = PROFILING_DIR / file_name
    with open(file_path, "r") as file:
        return json.load(file)


def _get_distribution_params(distribution: dict) -> tuple[list, list]:
    """Retrive or precompute the population and cumulative weights for a distribution."""

    dist_id = id(distribution)
    cached = _DISTRIBUTION_PARAMS_CACHE.get(dist_id)

    if cached is None:
        population = list(distribution.keys())
        cum_weights = list(itertools.accumulate(distribution.values()))
        cached = (population, cum_weights)
        _DISTRIBUTION_PARAMS_CACHE[dist_id] = cached

    return cached


def weighted_choice(distribution: dict) -> str:
    population, cum_weights = _get_distribution_params(distribution)
    target = random.random() * cum_weights[-1]
    index = bisect_right(cum_weights, target, 0, len(cum_weights)-1)
    return population[index]


def random_from_list(values: list) -> Any:
    return random.choice(values)
