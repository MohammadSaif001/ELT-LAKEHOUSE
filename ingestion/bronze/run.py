from ingestion.bronze.orders import ingest_orders
from ingestion.bronze.order_items import ingest_order_items
from ingestion.bronze.payments import ingest_payments
from ingestion.bronze.reviews import ingest_reviews
from ingestion.bronze.sellers import ingest_sellers
from ingestion.bronze.geolocation import ingest_geolocation
from ingestion.bronze.customers import ingest_customers
from spark.common.spark_session import create_spark_session

def bronze_runner() -> None:
    """Run all ingestion functions."""
    spark = create_spark_session()
    try:
        ingest_orders(spark)
        ingest_order_items(spark)
        ingest_payments(spark)
        ingest_reviews(spark)
        ingest_sellers(spark)
        ingest_geolocation(spark)
        ingest_customers(spark)
        print("All ingestion functions completed successfully.")
    except Exception as e:
        print(f"Ingestion failed: {e}")
        raise
    finally:
        spark.stop()
if __name__ == "__main__":
    bronze_runner()