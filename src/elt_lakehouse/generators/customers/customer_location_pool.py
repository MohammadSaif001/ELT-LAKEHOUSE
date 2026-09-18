from src.elt_lakehouse.generators.base.pool_manager import load_pool_column, save_pool
from src.elt_lakehouse.generators.customers.customer_location_generator import (
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
        customers: list = load_pool_column("customer_pool.parquet", "customer_id")

        locations: list = []
        for customer in customers:
            locations.append(generate_customer_location(customer))

        save_pool(locations, "customer_location_pool.parquet")
        logger.info(
            "Customer location pool generated and saved successfully to %s",
            "customer_location_pool.parquet",
        )
    except Exception:
        logger.exception(
            "Customer location pool generation failed : pool=%s",
            "customer_pool.parquet",
        )
        raise
