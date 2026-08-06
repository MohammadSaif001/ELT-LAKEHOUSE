import json
from functools import lru_cache
from spark.common.paths import POOLS_DIR 

#==============================
# Pool loading function
#==============================
@lru_cache(maxsize=None)
def load_pool(file_name: str) -> list:
    file_path = POOLS_DIR / file_name
    with open(file_path, "r") as file:
        return json.load(file)


#==============================
# Pool saving function
#==============================
def save_pool(pool: list, file_name: str) -> None:
    file_path = POOLS_DIR / file_name
    with open(file_path, "w") as file:
        json.dump(pool, file, indent=4)
