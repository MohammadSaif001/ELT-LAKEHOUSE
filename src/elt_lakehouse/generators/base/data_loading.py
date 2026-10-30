from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
from pathlib import Path

import pyarrow.parquet as pq

from src.elt_lakehouse.spark.common.paths import GENERATED_DIR


class GeneratedDataLoader:
    def __init__(self, base_dir: str | Path = GENERATED_DIR):
        self.base_dir = Path(base_dir)
        logger.debug("Initialized generated-data loader: base_dir=%s", self.base_dir)

    def load_generated_data(
        self, file_name: str, base_dir: str | Path = GENERATED_DIR
    ) -> list[dict]:
        """Loads generated data from a generated-data directory, supporting Parquet and JSON."""
        dir_path = Path(base_dir)
        name_no_ext = Path(file_name).stem

        parquet_path = dir_path / f"{name_no_ext}.parquet"
        if parquet_path.exists():
            table = pq.read_table(parquet_path)
            logger.info(
                "Loaded generated data: path=%s rows=%d", parquet_path, table.num_rows
            )
            return table.to_pylist()

        logger.error("Generated data file missing: path=%s", parquet_path)
        raise FileNotFoundError(f"Generated data file not found: {parquet_path}")

    def column_from_generated_data(
        self, file_name: str, column_name: str, base_dir: str | Path = GENERATED_DIR
    ) -> list[str]:
        """Load a specific column from a generated data Parquet file."""
        dir_path = Path(base_dir)
        name_no_ext = Path(file_name).stem
        parquet_path = dir_path / f"{name_no_ext}.parquet"
        if parquet_path.exists():
            table = pq.read_table(parquet_path, columns=[column_name])
            logger.info(
                "Loaded generated-data column: path=%s column=%s rows=%d",
                parquet_path,
                column_name,
                table.num_rows,
            )
            return table[column_name].to_pylist()

        logger.error("Generated data file missing: path=%s", parquet_path)
        raise FileNotFoundError(f"Generated data file not found: {parquet_path}")


_generated_data_loader = GeneratedDataLoader()


def load_generated_data(
    file_name: str, base_dir: str | Path = GENERATED_DIR
) -> list[dict]:
    """Load generated data from Parquet, caching repeated reads in this process."""
    logger.info("load_generated_data started")
    return _generated_data_loader.load_generated_data(file_name, base_dir=base_dir)


def load_generated_data_column(
    file_name: str, column_name: str, base_dir: str | Path = GENERATED_DIR
) -> list[str]:
    """Load a specific column from a generated data Parquet file."""
    logger.info("load_generated_data_column started")
    return _generated_data_loader.column_from_generated_data(
        file_name, column_name, base_dir=base_dir
    )
