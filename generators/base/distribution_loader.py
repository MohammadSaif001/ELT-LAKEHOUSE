#generators/base/distribution_loader.py
import json
import random
from pathlib import Path
from spark.common.paths import (
    PROFILING_DIR,
    ORDER_ITEM_PROFILING_DIR
)


def load_distribution(file_name: str) -> dict:
    file_path = (
        PROFILING_DIR / file_name
    )
    with open(file_path, "r") as file:
        return json.load(file)

def weighted_choice(distribution: dict):
    return random.choices(
        population = list(distribution.keys()),
        weights=list(distribution.values()),
        k=1
    )[0]

def random_from_list(values: list):
    return random.choice(values)