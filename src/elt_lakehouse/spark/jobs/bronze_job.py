from datetime import datetime
from collections.abc import Callable
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.ingestion.bronze.orders import ingest_orders
from src.elt_lakehouse.ingestion.bronze.reviews import ingest_reviews
from src.elt_lakehouse.ingestion.bronze.sellers import ingest_sellers
from src.elt_lakehouse.ingestion.bronze.payments import ingest_payments
from src.elt_lakehouse.ingestion.bronze.products import ingest_products
from src.elt_lakehouse.ingestion.bronze.customers import ingest_customers
from src.elt_lakehouse.ingestion.bronze.geolocation import ingest_geolocation
from src.elt_lakehouse.ingestion.bronze.order_items import ingest_order_items
from src.elt_lakehouse.spark.common.spark_session import create_spark_session

logger = get_logger(__name__)


def run_bronze_ingestion() -> None:
    """Run all ingestion functions."""
    started_at: datetime = datetime.now()
    spark = create_spark_session()
    logger.info("Starting bronze ingestion.")
    generators: list[tuple[str, Callable]] = [
        ("customers", ingest_customers),
        ("geolocations", ingest_geolocation),
        ("orders", ingest_orders),
        ("order items", ingest_order_items),
        ("payments", ingest_payments),
        ("reviews", ingest_reviews),
        ("sellers", ingest_sellers),
        ("products", ingest_products),
    ]
    try:
        for dataset_name, ingestion_function in generators:
            logger.info("Ingesting dataset:%s", dataset_name)
            ingestion_function(spark)

        duration_seconds: float = (datetime.now() - started_at).total_seconds()
        logger.info(
            "All ingestion functions completed successfully in duration_s=%.2f",
            duration_seconds,
        )
    except Exception:
        logger.exception("Ingestion failed.")
        raise
    finally:
        spark.stop()


def main():
    run_bronze_ingestion()


if __name__ == "__main__":
    main()
