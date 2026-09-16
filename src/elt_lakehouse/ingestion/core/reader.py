import logging

from pyspark.sql import DataFrame, SparkSession

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.utils.memory import monitor_memory

logger = get_logger(__name__)


# ===============================
# Read Parquet into DataFrame
# ===============================
@monitor_memory
def read_parquet(spark: SparkSession, input_path: str) -> DataFrame:
    """Read a Parquet file into a Spark DataFrame."""
    try:
        logger.info("Reading Parquet into DataFrame: path=%s", input_path)

        df = spark.read.parquet(input_path)

        logger.info(
            "DataFrame created: path=%s, columns=%d",
            input_path,
            len(df.columns),
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "DataFrame row count: path=%s, rows=%d",
                input_path,
                df.count(),
            )

        return df

    except Exception:
        logger.exception("Failed to read Parquet into DataFrame: path=%s", input_path)
        raise


# ===============================
# Read JSON into DataFrame
# ===============================
@monitor_memory
def read_json(spark: SparkSession, input_path: str) -> DataFrame:
    """Read a JSON file into a Spark DataFrame, delegating to Parquet if available."""
    try:
        from pathlib import Path

        path_obj = Path(input_path)
        if path_obj.suffix == ".parquet":
            return read_parquet(spark, input_path)

        parquet_alt = path_obj.with_suffix(".parquet")
        if not path_obj.exists() and parquet_alt.exists():
            return read_parquet(spark, str(parquet_alt))

        logger.info("Reading JSON into DataFrame: path=%s", input_path)

        df = spark.read.option("multiLine", "true").json(input_path)

        logger.info(
            "DataFrame created: path=%s, columns=%d",
            input_path,
            len(df.columns),
        )

        # this triggers a Spark job.
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


# ===============================
# Read Delta into DataFrame
# ===============================


def read_delta(spark: SparkSession, input_path: str) -> DataFrame:
    try:
        logger.info("Reading Delta into DataFrame: path=%s", input_path)

        df = spark.read.format("delta").load(input_path)

        logger.info(
            "DataFrame created: path=%s, columns=%d",
            input_path,
            len(df.columns),
        )

        # this triggers a Spark job.
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "DataFrame row count: path=%s, rows=%d",
                input_path,
                df.count(),
            )

        return df
    except Exception:
        logger.exception("Failed to read Delta into DataFrame: path=%s", input_path)
        raise
