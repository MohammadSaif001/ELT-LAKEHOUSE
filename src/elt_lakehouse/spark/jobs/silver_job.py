from datetime import datetime, timezone

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.spark_session import create_spark_session
from src.elt_lakehouse.spark.silver.customers_silver import process_customers
from src.elt_lakehouse.spark.silver.geo_location_silver import process_geolocation
from src.elt_lakehouse.spark.silver.order_item_silver import process_order_items
from src.elt_lakehouse.spark.silver.orders_silver import process_orders
from src.elt_lakehouse.spark.silver.payments_silver import process_payments
from src.elt_lakehouse.spark.silver.product_silver import process_products
from src.elt_lakehouse.spark.silver.reviews_silver import process_reviews
from src.elt_lakehouse.spark.silver.sellers_silver import process_sellers

logger =  get_logger(__name__)


def run_silver_processing() -> None:
    """Run the silver layer processing for all datasets."""
    logger.info("Starting silver layer processing...")
    started_at: datetime = datetime.now(timezone.utc)
    spark = create_spark_session()
    try:
        process_customers(spark)
        process_payments(spark)
        process_orders(spark)
        process_reviews(spark)
        process_order_items(spark)
        process_sellers(spark)
        process_products(spark)
        process_geolocation(spark)

        logger.info("Silver layer processing completed successfully.")
        duration_seconds: float = (datetime.now(timezone.utc) - started_at).total_seconds()
        logger.info(
                    "All data validations completed successfully in duration_s=%.2f",
                    duration_seconds,
                )
    except Exception:
        logger.exception("Silver layer processing failed.")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    run_silver_processing()
