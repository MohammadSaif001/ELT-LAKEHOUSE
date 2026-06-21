import json
from spark.common.paths import GENERATED_DIR

def load_generated_data(file_name: str) -> list:
    """Loads generated data from storage/generated/."""
    file_path = GENERATED_DIR / file_name
    with open(file_path, "r") as file:
        return json.load(file)