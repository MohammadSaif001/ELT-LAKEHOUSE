from pyspark.sql import SparkSession
from config.config_loader import load_yaml
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.ingestion.core.ingestor import ingestor

logger = get_logger(__name__)

INPUT_PATH = "storage/generated/generated_reviews_data.json"
OUTPUT_PATH = "storage/bronze/reviews_delta"
GEN_CONFIG = load_yaml("spark_config.yaml")["spark"]["bronze"]


def ingest_reviews(spark: SparkSession) -> None:
    """Ingest generated reviews JSON data into a Bronze Delta table."""

    try:
        logger.info(
            "Starting reviews ingestion: input_path=%s, output_path=%s",
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
            "Reviews ingestion completed successfully: output_path=%s",
            OUTPUT_PATH,
        )

    except Exception:
        logger.exception(
            "Reviews ingestion failed: input_path=%s, output_path=%s",
            INPUT_PATH,
            OUTPUT_PATH,
        )
        raise
