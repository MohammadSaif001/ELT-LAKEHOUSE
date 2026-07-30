import logging
from pyspark.sql import DataFrame, SparkSession
from spark.common.logger import get_logger

logger = get_logger("ingestion.common.reader")

#===============================
# Read JSON into DataFrame
#===============================
def read_json(spark: SparkSession, input_path: str) -> DataFrame:
    """Read a JSON file into a Spark DataFrame."""
    try:
        logger.info("Reading JSON into DataFrame: path=%s", input_path)

        df = (
            spark.read
            .option("multiLine", "true")
            .json(input_path)
        )

        logger.info(
            "DataFrame created: path=%s, columns=%d",
            input_path,
            len(df.columns),
        )

        # Count only for detailed diagnostics; this triggers a Spark job.
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "DataFrame row count: path=%s, rows=%d",
                input_path,
                df.count(),
            )

        return df

    except Exception:
        logger.exception("Failed to read JSON into DataFrame: path=%s", input_path)
        raise