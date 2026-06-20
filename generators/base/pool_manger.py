import json
from spark.common.paths import POOLS_DIR

def load_pool(file_name: str) -> list:
    file_path = POOLS_DIR / file_name
    with open(file_path, "r") as file:
        return json.load(file)

def save_pool(pool: list, file_name: str):
    file_path = POOLS_DIR / file_name
    with open(file_path, "w") as file:
        json.dump(pool, file, indent=4)
        