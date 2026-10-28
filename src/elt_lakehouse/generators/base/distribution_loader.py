
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
import itertools
import json
import random
from typing import Any
from bisect import bisect_right
from src.elt_lakehouse.spark.common.paths import PROFILING_DIR

_DISTRIBUTION_PARAMS_CACHE: dict[int, tuple[list, list]] = {}


def load_distribution(file_name: str) -> dict:
    file_path = PROFILING_DIR / file_name
    logger.info("Loading distribution: path=%s", file_path)
    try:
        with open(file_path, "r") as file:
            distribution = json.load(file)
    except OSError:
        logger.exception("Failed to read distribution: path=%s", file_path)
        raise
    logger.info("Loaded distribution: path=%s entries=%d", file_path, len(distribution))
    return distribution


def _get_distribution_params(distribution: dict) -> tuple[list, list]:
    """Retrive or precompute the population and cumulative weights for a distribution."""

    dist_id = id(distribution)
    cached = _DISTRIBUTION_PARAMS_CACHE.get(dist_id)

    if cached is None:
        population = list(distribution.keys())
        cum_weights = list(itertools.accumulate(distribution.values()))
        cached = (population, cum_weights)
        _DISTRIBUTION_PARAMS_CACHE[dist_id] = cached
        logger.debug("Prepared distribution weights: entries=%d", len(population))

    return cached


def weighted_choice(distribution: dict) -> str:
    population, cum_weights = _get_distribution_params(distribution)
    target = random.random() * cum_weights[-1]
    index = bisect_right(cum_weights, target, 0, len(cum_weights)-1)
    return population[index]


def random_from_list(values: list) -> Any:
    return random.choice(values)
