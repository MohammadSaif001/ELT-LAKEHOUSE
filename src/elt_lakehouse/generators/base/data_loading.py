from pathlib import Path

import pyarrow.parquet as pq

from src.elt_lakehouse.spark.common.paths import GENERATED_DIR


class GeneratedDataLoader:
    def __init__(self, base_dir: str | Path = GENERATED_DIR):
        self.base_dir = Path(base_dir)

    def load_generated_data(
        self, file_name: str, base_dir: str | Path = GENERATED_DIR
    ) -> list[dict]:
        """Loads generated data from a generated-data directory, supporting Parquet and JSON."""
        dir_path = Path(base_dir)
        name_no_ext = Path(file_name).stem

        parquet_path = dir_path / f"{name_no_ext}.parquet"
        if parquet_path.exists():
            table = pq.read_table(parquet_path)
            return table.to_pylist()

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
            return table[column_name].to_pylist()

        raise FileNotFoundError(f"Generated data file not found: {parquet_path}")


_generated_data_loader = GeneratedDataLoader()


def load_generated_data(
    file_name: str, base_dir: str | Path = GENERATED_DIR
) -> list[dict]:
    """Load generated data from Parquet, caching repeated reads in this process."""
    return _generated_data_loader.load_generated_data(file_name, base_dir=base_dir)


def load_generated_data_column(
    file_name: str, column_name: str, base_dir: str | Path = GENERATED_DIR
) -> list[str]:
    """Load a specific column from a generated data Parquet file."""
    return _generated_data_loader.column_from_generated_data(
        file_name, column_name, base_dir=base_dir
    )
