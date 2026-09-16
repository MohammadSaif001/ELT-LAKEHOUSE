import shutil
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

from src.elt_lakehouse.generators.base.data_saving import save_generated_data
from src.elt_lakehouse.generators.base.pool_manager import load_pool
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import POOLS_DIR

logger = get_logger(__name__)

# =========================
# Product Builder
# =========================


def build_products(output_dir: str) -> None:
    """Loads product pool data and saves it to the generated datasets folder."""
    pool_file: str = "product_pool.parquet"
    output_file: str = "generated_products_data.parquet"
    started_at: datetime = datetime.now(timezone.utc)

    try:
        pool_path = POOLS_DIR / pool_file
        dest_path = Path(output_dir) / output_file
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if pool_path.exists():
            shutil.copyfile(pool_path, dest_path)
            record_count = pq.read_metadata(dest_path).num_rows
        else:
            products = load_pool("product_pool")
            record_count = len(products)
            save_generated_data(products, output_file, output_dir)

        duration_seconds: float = (
            datetime.now(timezone.utc) - started_at
        ).total_seconds()
        logger.info(
            "Product dataset generated successfully: records=%d, path=%s/%s, duration_s=%.2f",
            record_count,
            output_dir,
            output_file,
            duration_seconds,
        )
    except Exception:
        logger.exception(
            "Product dataset generation failed: pool_file=%s, output_dir=%s",
            pool_file,
            output_dir,
        )
        raise
