import json
from pathlib import Path

import pyarrow.parquet as pq

from src.elt_lakehouse.spark.common.paths import GENERATED_DIR


def load_generated_data(file_name: str, base_dir: str | Path = GENERATED_DIR) -> list:
    """Loads generated data from a generated-data directory, supporting Parquet and JSON."""
    dir_path = Path(base_dir)
    name_no_ext = Path(file_name).stem

    parquet_path = dir_path / f"{name_no_ext}.parquet"
    if parquet_path.exists():
        table = pq.read_table(parquet_path)
        return table.to_pylist()

    direct_path = dir_path / file_name
    if direct_path.exists():
        if direct_path.suffix == ".parquet":
            table = pq.read_table(direct_path)
            return table.to_pylist()
        with open(direct_path, "r", encoding="utf-8") as file:
            return json.load(file)

    json_path = dir_path / f"{name_no_ext}.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as file:
            return json.load(file)

    raise FileNotFoundError(f"Generated data file not found: {parquet_path}")
