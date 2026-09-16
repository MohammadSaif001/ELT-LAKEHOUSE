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
