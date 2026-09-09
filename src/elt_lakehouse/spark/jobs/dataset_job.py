from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from src.elt_lakehouse.generators.customers.build_customers import build_customers
from src.elt_lakehouse.generators.customers.build_geolocations import build_geolocations
from src.elt_lakehouse.generators.orders.build_orders import (
    build_order_items,
    build_orders,
)
from src.elt_lakehouse.generators.payments.build_payments import build_payments
from src.elt_lakehouse.generators.products.build_products import build_products
from src.elt_lakehouse.generators.reviews.build_reviews import build_reviews
from src.elt_lakehouse.generators.sellers.build_sellers import build_sellers
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

# =======================
# Build Dataset
# =======================


def run_dataset_job(output_dir: str = "storage/generated") -> None:
    start_time: datetime = datetime.now(timezone.utc)
    output_path = Path(output_dir)
    logger.info(
        "Starting dataset generation. Output directory=%s",
        output_path,
    )

    generators: list[tuple[str, Callable]] = [
        ("customers", build_customers),
        ("geolocations", build_geolocations),
        ("sellers", build_sellers),
        ("products", build_products),
        ("orders", build_orders),
        ("order items", build_order_items),
        ("payments", build_payments),
        ("reviews", build_reviews),
    ]

    try:
        for dataset_name, build_function in generators:
            logger.info("Generating dataset:%s", dataset_name)
            build_function(output_path)

        elapsed: float = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            "Dataset generation completed successfully in duration_s=%.2f",
            elapsed,
        )
    except Exception:
        logger.exception("An error occurred during dataset generation.")
        raise


def main() -> None:
    run_dataset_job()


if __name__ == "__main__":
    main()
