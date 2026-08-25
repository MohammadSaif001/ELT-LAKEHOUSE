from pyspark.sql import SparkSession
from config.config_loader import load_yaml
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.ingestion.core.ingestor import ingestor

logger = get_logger(__name__)

INPUT_PATH = "storage/generated/generated_geolocation_data.json"
OUTPUT_PATH = "storage/bronze/geolocation_delta"
GEN_CONFIG = load_yaml("spark_config.yaml")["spark"]["bronze"]


def ingest_geolocation(spark: SparkSession) -> None:
    """Ingest generated geolocation JSON data into a Bronze Delta table."""

    try:
        logger.info(
            "Starting geolocation ingestion: input_path=%s, output_path=%s",
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
            "Geolocation ingestion completed successfully: output_path=%s",
            OUTPUT_PATH,
        )

    except Exception:
        logger.exception(
            "Geolocation ingestion failed: input_path=%s, output_path=%s",
            INPUT_PATH,
            OUTPUT_PATH,
        )
        raise
