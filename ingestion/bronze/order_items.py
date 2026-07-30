from pyspark.sql import SparkSession
from spark.common.logger import get_logger
from ingestion.common.ingestor import ingestor



logger = get_logger("ingestion.bronze.order_items")

INPUT_PATH = "storage/generated/generated_order_items_data.json"
OUTPUT_PATH = "storage/bronze/order_items_delta"

def ingest_order_items(spark : SparkSession) -> None:
    """Ingest generated order items JSON data into a Bronze Delta table."""

    try:
        logger.info(
            "Starting order items ingestion: input_path=%s, output_path=%s",
            INPUT_PATH,
            OUTPUT_PATH,
        )


        ingestor(
            input_path=INPUT_PATH,
            output_path=OUTPUT_PATH,
            spark=spark,
            mode="overwrite",
        )

        logger.info(
            "Order items ingestion completed successfully: output_path=%s",
            OUTPUT_PATH,
        )

    except Exception:
        logger.exception(
            "Order items ingestion failed: input_path=%s, output_path=%s",
            INPUT_PATH,
            OUTPUT_PATH,
        )
        raise


