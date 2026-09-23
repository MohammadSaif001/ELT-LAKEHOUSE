from collections.abc import Callable
from datetime import datetime, timezone

from src.elt_lakehouse.generators.geolocation.customer_location_pool import (
    build_customer_location_pool,
)
from src.elt_lakehouse.generators.customers.customer_pool import build_customers_pool
from src.elt_lakehouse.generators.products.product_pool import build_product_pool
from src.elt_lakehouse.generators.sellers.seller_pool import build_seller_pool
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import POOLS_DIR
from src.elt_lakehouse.spark.utils.memory import monitor_memory

logger = get_logger(__name__)


# ==========================
# Build Pool
# ==========================


@monitor_memory
def run_pool_job() -> None:
    start_time: datetime = datetime.now(timezone.utc)
    POOLS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Starting pool generation...")
    generators: list[tuple[str, Callable]] = [
        ("customers", build_customers_pool),
        ("products", build_product_pool),
        ("customer locations", build_customer_location_pool),
        ("sellers", build_seller_pool),
    ]

    try:
        for pool_name, build_function in generators:
            logger.info("Generating pool: %s", pool_name)
            build_function()
        elapsed: float = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            "Pool generation completed successfully in duration_s=%.2f",
            elapsed,
        )
    except Exception:
        logger.exception("An error occurred during pool generation.")
        raise


def main() -> None:
    run_pool_job()


if __name__ == "__main__":
    main()
