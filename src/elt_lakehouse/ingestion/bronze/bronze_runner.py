from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.ingestion.bronze.orders import ingest_orders
from src.elt_lakehouse.ingestion.bronze.reviews import ingest_reviews
from src.elt_lakehouse.ingestion.bronze.sellers import ingest_sellers
from src.elt_lakehouse.ingestion.bronze.payments import ingest_payments
from src.elt_lakehouse.ingestion.bronze.customers import ingest_customers
from src.elt_lakehouse.ingestion.bronze.geolocation import ingest_geolocation
from src.elt_lakehouse.ingestion.bronze.order_items import ingest_order_items
from src.elt_lakehouse.spark.common.spark_session import create_spark_session

logger = get_logger("ingestion.bronze.run")

def bronze_runner() -> None:
    """Run all ingestion functions."""
    spark = create_spark_session()
    try:
        logger.info("Starting ingestion functions...")
        ingest_orders(spark)
        ingest_order_items(spark)
        ingest_payments(spark)
        ingest_reviews(spark)
        ingest_sellers(spark)
        ingest_geolocation(spark)
        ingest_customers(spark)
        logger.info("All ingestion functions completed successfully.")
    except Exception:
        logger.exception("Ingestion failed.")
        raise
    finally:
        spark.stop()
        
def main():
    bronze_runner()

if __name__ == "__main__":
    main()