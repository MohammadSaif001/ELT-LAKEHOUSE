from datetime import datetime
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.base.pool_manager import load_pool
from src.elt_lakehouse.generators.base.data_saving import save_generated_data

logger = get_logger(__name__)
# ===========================
# Customer Builder
# ===========================


def build_customers(output_dir: str) -> None:
    """Load the customer pool and save it as a generated dataset."""
    pool_name = "customer_pool.json"
    output_name = "generated_customers_data.json"
    started_at: datetime = datetime.now()
    try:
        logger.info("Loading customer pool from %s", pool_name)
        customers = load_pool(pool_name)
        logger.info(
            "Saving generated customer dataset: records=%d, file=%s, output_dir=%s",
            len(customers),
            output_name,
            output_dir,
        )

        save_generated_data(customers, output_name, output_dir)
        duration_seconds: float = (datetime.now() - started_at).total_seconds()
        logger.info(
            "Customer dataset generated successfully: records=%d, path=%s/%s, duration_s=%.2f",
            len(customers),
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
