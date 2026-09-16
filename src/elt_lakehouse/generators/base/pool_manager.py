import json
from functools import cache
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.elt_lakehouse.spark.common.paths import POOLS_DIR


# ==============================
# Pool loading function
# ==============================
@cache
def load_pool(file_name: str) -> list:
    name_no_ext = Path(file_name).stem
    parquet_path = POOLS_DIR / f"{name_no_ext}.parquet"
    if parquet_path.exists():
        table = pq.read_table(parquet_path)
        return table.to_pylist()

    direct_path = POOLS_DIR / file_name
    if direct_path.exists():
        if direct_path.suffix == ".parquet":
            table = pq.read_table(direct_path)
            return table.to_pylist()
        with open(direct_path, "r", encoding="utf-8") as file:
            return json.load(file)

    json_path = POOLS_DIR / f"{name_no_ext}.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as file:
            return json.load(file)

    raise FileNotFoundError(f"Pool file not found: {parquet_path}")


# ==============================
# Pool saving function
# ==============================
def save_pool(pool: list, file_name: str) -> None:
    name_no_ext = Path(file_name).stem
    parquet_path = POOLS_DIR / f"{name_no_ext}.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(pool)
    pq.write_table(table, parquet_path)
