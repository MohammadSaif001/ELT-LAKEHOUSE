from functools import cache
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.elt_lakehouse.spark.common.paths import POOLS_DIR


# ==============================
# Pool loading function
# ==============================
class PoolLoader:
    """A class for loading pool data from parquet files."""

    def __init__(self, pools_dir: Path = POOLS_DIR):
        self.pools_dir = pools_dir

    @cache
    def load_pool(self, file_name: str) -> list[dict]:
        name_no_ext = Path(file_name).stem
        parquet_path = self.pools_dir / f"{name_no_ext}.parquet"
        if parquet_path.exists():
            table = pq.read_table(parquet_path)
            return table.to_pylist()

        raise FileNotFoundError(f"Pool file not found: {parquet_path}")

    @cache
    def pool_column(self, file_name: str, column_name: str) -> list:
        """Load a specific column from a pool parquet file."""
        name_no_ext = Path(file_name).stem
        parquet_path = self.pools_dir / f"{name_no_ext}.parquet"
        if parquet_path.exists():
            table = pq.read_table(parquet_path, columns=[column_name])
            return table[column_name].to_pylist()

        raise FileNotFoundError(f"Pool file not found: {parquet_path}")


_pool_loader = PoolLoader()


def load_pool(file_name: str) -> list[dict]:
    """Load a pool from Parquet, caching repeated reads in this process."""
    return _pool_loader.load_pool(file_name)


def load_pool_column(file_name: str, column_name: str):
    """Load a specific column from a pool parquet file."""
    return _pool_loader.pool_column(file_name, column_name)


# ==============================
# Pool saving function
# ==============================
def save_pool(pool: list, file_name: str) -> None:
    name_no_ext = Path(file_name).stem
    parquet_path = POOLS_DIR / f"{name_no_ext}.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(pool)
    pq.write_table(table, parquet_path)
