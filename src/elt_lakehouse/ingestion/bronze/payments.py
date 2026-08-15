from pyspark.sql import SparkSession
from config.config_loader import load_yaml
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.ingestion.core.ingestor import ingestor



logger = get_logger("ingestion.bronze.payments")

INPUT_PATH = "storage/generated/generated_payments_data.json"
OUTPUT_PATH = "storage/bronze/payments_delta"
GEN_CONFIG = load_yaml("spark_config.yaml")["spark"]["bronze"]

def ingest_payments(spark : SparkSession) -> None:
    """Ingest payments order JSON data into a Bronze Delta table."""

    try:
        logger.info(
            "Starting payment ingestion: input_path=%s, output_path=%s",
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
            "Payment ingestion completed successfully: output_path=%s",
            OUTPUT_PATH,
        )

    except Exception:
        logger.exception(
            "Payment ingestion failed: input_path=%s, output_path=%s",
            INPUT_PATH,
            OUTPUT_PATH,
        )
        raise


