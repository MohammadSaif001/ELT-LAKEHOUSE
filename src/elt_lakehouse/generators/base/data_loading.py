import json
from pathlib import Path
from src.elt_lakehouse.spark.common.paths import GENERATED_DIR

def load_generated_data(file_name: str, base_dir: str | Path = GENERATED_DIR) -> list:
    """Loads generated data from a generated-data directory."""
    file_path = Path(base_dir) / file_name
    with open(file_path, "r") as file:
        return json.load(file)