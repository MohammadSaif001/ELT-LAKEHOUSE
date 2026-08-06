from pyspark.sql import SparkSession
from config.config_loader import load_yaml
from spark.common.logger import get_logger
from ingestion.core.ingestor import ingestor



logger = get_logger("ingestion.bronze.orders")

INPUT_PATH = "storage/generated/generated_orders_data.json"
OUTPUT_PATH = "storage/bronze/orders_delta"
GEN_CONFIG = load_yaml("spark_config.yaml")["spark"]["bronze"]

def ingest_orders(spark : SparkSession) -> None:
    """Ingest generated order JSON data into a Bronze Delta table."""


    try:
        logger.info(
            "Starting order ingestion: input_path=%s, output_path=%s",
            INPUT_PATH,
            OUTPUT_PATH,
        )


        ingestor(
            input_path=INPUT_PATH,
            output_path=OUTPUT_PATH,
            spark=spark,
            mode=GEN_CONFIG["mode"],
        )

        logger.info(
            "Order ingestion completed successfully: output_path=%s",
            OUTPUT_PATH,
        )

    except Exception:
        logger.exception(
            "Order ingestion failed: input_path=%s, output_path=%s",
            INPUT_PATH,
            OUTPUT_PATH,
        )
        raise
