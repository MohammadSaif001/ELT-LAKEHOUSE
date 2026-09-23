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


def iter_pool_batches(file_name: str, batch_size: int = 10_000):
    """Yield pool rows in bounded batches without loading the whole pool."""
    name_no_ext = Path(file_name).stem
    parquet_path = POOLS_DIR / f"{name_no_ext}.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Pool file not found: {parquet_path}")
    parquet_file = pq.ParquetFile(parquet_path)
    for record_batch in parquet_file.iter_batches(batch_size=batch_size):
        yield record_batch.to_pylist()


# ==============================
# Pool saving function
# ==============================
def save_pool(pool: list, file_name: str) -> None:
    name_no_ext = Path(file_name).stem
    parquet_path = POOLS_DIR / f"{name_no_ext}.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(pool)
    pq.write_table(table, parquet_path)


def save_pool_batches(pool_batches, file_name: str) -> int:
    """Write batches of pool rows incrementally and return the row count."""
    name_no_ext = Path(file_name).stem
    parquet_path = POOLS_DIR / f"{name_no_ext}.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    writer = None
    row_count = 0
    try:
        for rows in pool_batches:
            if not rows:
                continue
            table = pa.Table.from_pylist(rows)
            if writer is None:
                writer = pq.ParquetWriter(parquet_path, table.schema)
            writer.write_table(table)
            row_count += table.num_rows
    finally:
        if writer is not None:
            writer.close()
    if writer is None:
        pq.write_table(pa.table({}), parquet_path)
    return row_count
