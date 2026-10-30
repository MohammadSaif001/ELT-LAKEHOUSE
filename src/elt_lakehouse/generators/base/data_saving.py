from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
from collections.abc import Iterable
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def save_generated_data(
    data: list, file_name: str, output_dir: str = "storage/generated"
) -> None:
    """Saves generated data list as a Parquet file in output_dir."""
    dir_path = Path(output_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    name_no_ext = Path(file_name).stem
    file_path = dir_path / f"{name_no_ext}.parquet"

    table = pa.Table.from_pylist(data)
    pq.write_table(table, file_path)
    logger.info("Saved generated data: path=%s rows=%d", file_path, table.num_rows)


def save_generated_batches(
    batches: Iterable[list[dict]],
    file_name: str,
    output_dir: str = "storage/generated",
) -> int:
    """Write bounded batches of rows to one Parquet file and return its row count."""
    dir_path = Path(output_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{Path(file_name).stem}.parquet"

    writer = None
    row_count = 0
    try:
        for rows in batches:
            if not rows:
                continue
            table = pa.Table.from_pylist(rows)

            if writer is None:
                writer = pq.ParquetWriter(file_path, table.schema)
            writer.write_table(table)
            row_count += table.num_rows
    finally:
        if writer is not None:
            writer.close()

    if writer is None:
        pq.write_table(pa.table({}), file_path)

    logger.info("Saved generated batches: path=%s rows=%d", file_path, row_count)
    return row_count


def write_tables(tables: Iterable[pa.Table], file_path: str | Path) -> int:
    """Stream Arrow tables into one Parquet file and return the row count.

    Later tables are cast to the first table's schema, so a chunk where a column
    happens to be all null does not break the file.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    writer = None
    row_count = 0
    try:
        for table in tables:
            if table.num_rows == 0:
                continue
            if writer is None:
                writer = pq.ParquetWriter(file_path, table.schema)
            elif not table.schema.equals(writer.schema):
                table = table.cast(writer.schema)
            writer.write_table(table)
            row_count += table.num_rows
    finally:
        if writer is not None:
            writer.close()

    if writer is None:
        pq.write_table(pa.table({}), file_path)

    logger.info("Saved tables: path=%s rows=%d", file_path, row_count)
    return row_count
