from collections.abc import Callable, Iterator

import pyarrow as pa

from src.elt_lakehouse.generators.base.data_saving import write_tables
from src.elt_lakehouse.generators.base.parallel import (
    base_seed,
    chunk_seed,
    map_chunks,
    rows_to_table,
    seed_this_process,
    split_counts,
    worker_count,
)
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import POOLS_DIR

logger = get_logger(__name__)

POOL_CHUNK_SIZE = 50_000


def _build_pool_chunk(task: tuple[Callable[[], dict], int, int]) -> pa.Table:
    """Worker: generate count pool rows with this chunk's own seed."""
    generator_function, count, seed = task
    seed_this_process(seed)
    return rows_to_table([generator_function() for _ in range(count)])


def _pool_tasks(
    generator_function: Callable[[], dict], size: int
) -> Iterator[tuple[Callable[[], dict], int, int]]:
    seed = base_seed()
    for index, count in enumerate(split_counts(size, POOL_CHUNK_SIZE)):
        yield generator_function, count, chunk_seed(seed, index)


def build_pool(
    generator_function: Callable[[], dict], pool_name: str, size: int
) -> int:
    """Generate size pool rows in parallel chunks, save them, return the row count.

    generator_function must be a module-level function so worker processes
    can import it. Rows are streamed to Parquet chunk by chunk, so the whole
    pool is never held in memory.
    """
    logger.info(
        "Building pool: name=%s size=%d workers=%d", pool_name, size, worker_count()
    )
    tables = map_chunks(_build_pool_chunk, _pool_tasks(generator_function, size))
    parquet_path = POOLS_DIR / f"{pool_name.removesuffix('.parquet')}.parquet"
    rows = write_tables(tables, parquet_path)
    logger.info("Pool built: name=%s rows=%d", pool_name, rows)
    return rows
