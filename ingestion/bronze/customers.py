from pyspark.sql import SparkSession
from spark.common.logger import get_logger
from ingestion.common.ingestor import ingestor



logger = get_logger("ingestion.bronze.customers")

INPUT_PATH = "storage/generated/generated_customers_data.json"
OUTPUT_PATH = "storage/bronze/customers_delta"


def ingest_customers(spark : SparkSession) -> None:
    """Ingest generated customer JSON data into a Bronze Delta table."""


    try:
        logger.info(
            "Starting customer ingestion: input_path=%s, output_path=%s",
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
            "Customer ingestion completed successfully: output_path=%s",
            OUTPUT_PATH,
        )

    except Exception:
        logger.exception(
            "Customer ingestion failed: input_path=%s, output_path=%s",
            INPUT_PATH,
            OUTPUT_PATH,
        )
        raise


        
