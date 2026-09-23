import shutil
from pathlib import Path

import pyarrow.parquet as pq

from src.elt_lakehouse.generators.base.data_saving import save_generated_data
from src.elt_lakehouse.generators.base.pool_manager import load_pool
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import POOLS_DIR

logger = get_logger(__name__)
# ===========================
# Geolocation Builder
# ===========================


def build_geolocations(output_dir: str) -> None:
    """Load the customer location pool and save it as a generated dataset."""
    
    pool_name = "customer_location_pool.parquet"
    output_name = "generated_geolocation_data.parquet"

    try:
        pool_path = POOLS_DIR / pool_name
        dest_path = Path(output_dir) / output_name
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if pool_path.exists():
            shutil.copyfile(pool_path, dest_path)
            record_count = pq.read_metadata(dest_path).num_rows
        else:
            locations = load_pool("customer_location_pool")
            record_count = len(locations)
            save_generated_data(locations, output_name, output_dir)

        logger.info(
            "Geolocation dataset generated successfully: records=%d, path=%s/%s",
            record_count,
            output_dir,
            output_name,
        )

    except Exception:
        logger.exception(
            "Geolocation dataset generation failed: pool=%s, output_dir=%s",
            pool_name,
            output_dir,
        )
        raise
