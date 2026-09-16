from datetime import datetime, timezone

from pyspark.sql import DataFrame
from pyspark.storagelevel import StorageLevel

from src.elt_lakehouse.ingestion.core.writer import write_delta
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import SILVER_DIR
from src.elt_lakehouse.spark.common.spark_session import create_spark_session
from src.elt_lakehouse.spark.quality.referential_integrity import (
    check_referential_integrity,
)
from src.elt_lakehouse.spark.silver.customers_silver import process_customers
from src.elt_lakehouse.spark.silver.geo_location_silver import process_geolocation
from src.elt_lakehouse.spark.silver.order_item_silver import process_order_items
from src.elt_lakehouse.spark.silver.orders_silver import process_orders
from src.elt_lakehouse.spark.silver.payments_silver import process_payments
from src.elt_lakehouse.spark.silver.product_silver import process_products
from src.elt_lakehouse.spark.silver.reviews_silver import process_reviews
from src.elt_lakehouse.spark.silver.sellers_silver import process_sellers
from src.elt_lakehouse.spark.utils.memory import monitor_memory

logger = get_logger(__name__)


@monitor_memory
def run_silver_processing(spark=None) -> None:
    """Run the silver layer processing for all datasets."""
    logger.info("Starting silver layer processing...")
    started_at: datetime = datetime.now(timezone.utc)
    own_spark = False
    if spark is None:
        spark = create_spark_session()
        own_spark = True
    try:
        customers_df = process_customers(spark)
        geolocation_df = process_geolocation(spark)
        orders_df = process_orders(spark)
        order_items_df = process_order_items(spark)
        payments_df = process_payments(spark)
        reviews_df = process_reviews(spark)
        products_df = process_products(spark)
        sellers_df = process_sellers(spark)

        # Persist parent lookup tables to prevent re-computing on each referential check
        customers_df = customers_df.persist(StorageLevel.MEMORY_AND_DISK)
        products_df = products_df.persist(StorageLevel.MEMORY_AND_DISK)
        sellers_df = sellers_df.persist(StorageLevel.MEMORY_AND_DISK)

        # Check referential integrity for each relationship

        orders_df, invalid_df = check_referential_integrity(
            orders_df, customers_df, "customer_id", "customer_id"
        )
        orders_df = orders_df.persist(StorageLevel.MEMORY_AND_DISK)
        write_delta(invalid_df, str(SILVER_DIR / "quarantine/orders_missing_customer"))

        order_items_df, invalid_df = check_referential_integrity(
            order_items_df, orders_df, "order_id", "order_id"
        )
        write_delta(
            invalid_df, str(SILVER_DIR / "quarantine/order_items_missing_order")
        )

        order_items_df, invalid_df = check_referential_integrity(
            order_items_df, products_df, "product_id", "product_id"
        )
        write_delta(
            invalid_df, str(SILVER_DIR / "quarantine/order_items_missing_product")
        )

        order_items_df, invalid_df = check_referential_integrity(
            order_items_df, sellers_df, "seller_id", "seller_id"
        )
        write_delta(
            invalid_df, str(SILVER_DIR / "quarantine/order_items_missing_seller")
        )

        payments_df, invalid_df = check_referential_integrity(
            payments_df, orders_df, "order_id", "order_id"
        )
        write_delta(invalid_df, str(SILVER_DIR / "quarantine/payments_missing_order"))

        reviews_df, invalid_df = check_referential_integrity(
            reviews_df, orders_df, "order_id", "order_id"
        )
        write_delta(invalid_df, str(SILVER_DIR / "quarantine/reviews_missing_order"))

        silver_outputs: dict[str, DataFrame] = {
            "customers_silver": customers_df,
            "geolocation_silver": geolocation_df,
            "orders_silver": orders_df,
            "order_items_silver": order_items_df,
            "payments_silver": payments_df,
            "reviews_silver": reviews_df,
            "products_silver": products_df,
            "sellers_silver": sellers_df,
        }
        for name, df in silver_outputs.items():
            write_delta(df, str(SILVER_DIR / name))

        customers_df.unpersist()
        products_df.unpersist()
        sellers_df.unpersist()
        orders_df.unpersist()

        logger.info("Silver layer processing completed successfully.")
        duration_seconds: float = (
            datetime.now(timezone.utc) - started_at
        ).total_seconds()
        logger.info(
            "All data validations completed successfully in duration_s=%.2f",
            duration_seconds,
        )
    except Exception:
        logger.exception("Silver layer processing failed.")
        raise
    finally:
        if own_spark:
            spark.stop()


if __name__ == "__main__":
    run_silver_processing()
