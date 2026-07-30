from pyspark.sql import SparkSession
from spark.common.logger import get_logger
from ingestion.common.ingestor import ingestor



logger = get_logger("ingestion.bronze.sellers")

INPUT_PATH = "storage/generated/generated_sellers_data.json"
OUTPUT_PATH = "storage/bronze/sellers_delta"

def ingest_sellers(spark : SparkSession) -> None:
    """Ingest generated seller JSON data into a Bronze Delta table."""

    try:
        logger.info(
            "Starting seller ingestion: input_path=%s, output_path=%s",
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
            "Seller ingestion completed successfully: output_path=%s",
            OUTPUT_PATH,
        )

    except Exception:
        logger.exception(
            "Seller ingestion failed: input_path=%s, output_path=%s",
            INPUT_PATH,
            OUTPUT_PATH,
        )
        raise


