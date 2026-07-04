import json
from pathlib import Path
from spark.common.paths import GENERATED_DIR

def save_generated_data(data: list, file_name: str, output_dir:str ="storage/generated")-> None:
    """Saves generated data list as a JSON file in storage/generated/."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    file_path = Path(output_dir) / file_name
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
