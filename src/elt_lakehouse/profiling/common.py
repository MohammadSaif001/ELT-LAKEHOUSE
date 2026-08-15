import csv
import json
import pandas as pd
from src.elt_lakehouse.spark.common.paths import RAW_DATA_DIR, PROFILING_DIR


def load_csv(file_name: str) -> pd.DataFrame:
    """Load a raw Olist CSV file with relaxed parsing to tolerate malformed rows."""
    csv_path = RAW_DATA_DIR / "olist" / file_name

    if file_name == "olist_order_reviews_dataset.csv":
        with csv_path.open("r", encoding="utf-8") as handle:
            lines : list[str] = [line.rstrip("\n") for line in handle if line.strip()]

        if not lines:
            return pd.DataFrame()

        header : list[str] = next(csv.reader([lines[0]], skipinitialspace=True))
        rows : list[list[str]] = []
        for line in lines[1:]:
            try:
                row = next(csv.reader([line], skipinitialspace=True))
            except csv.Error:
                continue
            if len(row) >= 7:
                rows.append(row[:7])

        return pd.DataFrame(rows, columns=header[:7])

    return pd.read_csv(
        csv_path,
        on_bad_lines="skip",
        engine="python",
    )


def save_profile(data: dict, file_name: str) -> None:
    """Save profiling metadata as formatted JSON."""
    output_path = PROFILING_DIR / file_name

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)