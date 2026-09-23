from src.elt_lakehouse.generators.base.pool_manager import (
    iter_pool_batches,
    save_pool_batches,
)
from elt_lakehouse.generators.geolocation.customer_location_generator import (
    generate_customer_location,
)
from src.elt_lakehouse.spark.common.logger import get_logger

# =================================
# Build Customer Location Pool
# =================================

logger = get_logger(__name__)


def build_customer_location_pool() -> None:
    """Generate a pool of customer locations based on the customer pool."""
    try:
        logger.info("Generating customer location pool from customer pool")

        def location_batches():
            for customers in iter_pool_batches("customer_pool.parquet"):
                yield [generate_customer_location(customer) for customer in customers]

        location_count = save_pool_batches(
            location_batches(), "customer_location_pool.parquet"
        )
        logger.info(
            "Customer location pool generated successfully: records=%d, file=%s",
            location_count,
            "customer_location_pool.parquet",
        )
    except Exception:
        logger.exception(
            "Customer location pool generation failed : pool=%s",
            "customer_pool.parquet",
        )
        raise
