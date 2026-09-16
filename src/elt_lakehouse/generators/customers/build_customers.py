import shutil
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

from src.elt_lakehouse.generators.base.data_saving import save_generated_data
from src.elt_lakehouse.generators.base.pool_manager import load_pool
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import POOLS_DIR

logger = get_logger(__name__)
# ===========================
# Customer Builder
# ===========================


def build_customers(output_dir: str) -> None:
    """Load the customer pool and save it as a generated dataset."""
    pool_name = "customer_pool.parquet"
    output_name = "generated_customers_data.parquet"
    started_at: datetime = datetime.now(timezone.utc)
    try:
        pool_path = POOLS_DIR / pool_name
        dest_path = Path(output_dir) / output_name
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if pool_path.exists():
            shutil.copyfile(pool_path, dest_path)
            record_count = pq.read_metadata(dest_path).num_rows
        else:
            customers = load_pool("customer_pool")
            record_count = len(customers)
            save_generated_data(customers, output_name, output_dir)

        duration_seconds: float = (
            datetime.now(timezone.utc) - started_at
        ).total_seconds()
        logger.info(
            "Customer dataset generated successfully: records=%d, path=%s/%s, duration_s=%.2f",
            record_count,
            output_dir,
            output_name,
            duration_seconds,
        )

    except Exception:
        logger.exception(
            "Customer dataset generation failed: pool=%s, output_dir=%s",
            pool_name,
            output_dir,
        )
        raise
