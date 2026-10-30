import os
from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.utils.memory import monitor_memory

logger = get_logger(__name__)


# ===============================
# Write DataFrame to Delta Lake
# ===============================


# currently using overwrite because we are not using kafka to stream data, so we are not appending data to the delta table.
@monitor_memory
def write_delta(df: DataFrame, output_path: str, mode: str = "overwrite") -> None:
    """Write a Spark DataFrame to Delta Lake format."""
    try:
        DATAFRAME_LENGTH = len(df.columns)
        logger.info(
            "Writing DataFrame to Delta Lake: path=%s, mode=%s, columns=%d",
            output_path,
            mode,
            DATAFRAME_LENGTH,
        )

        df.write.format("delta").mode(mode).save(output_path)

        logger.info(
            "DataFrame written to Delta Lake: path=%s, columns=%d",
            output_path,
            DATAFRAME_LENGTH,
        )

    except Exception:
        logger.exception(
            "Failed to write DataFrame to Delta Lake: path=%s, mode=%s",
            output_path,
            mode,
        )
        raise


# ==============================
# Write DataFrame to Postgres
# ==============================


def _jdbc_connection() -> tuple[str, str, str]:
    """Return (jdbc_url, user, password) from environment variables."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "elt_lakehouse")
    user = os.getenv("POSTGRES_USER", "pipeline_writer")
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("POSTGRES_PASSWORD environment variable is not set.")
    # rewriteBatchedInserts turns batches into multi-row INSERTs (much faster).
    url = f"jdbc:postgresql://{host}:{port}/{database}?rewriteBatchedInserts=true"
    return url, user, password


def write_postgres(
    df: DataFrame,
    table_name: str,
    mode: str = "overwrite",
    schema: str = "gold",
    truncate: bool = True,
    batch_size: int = 10_000,
    num_partitions: int = 4,
) -> None:
    """Write a Spark DataFrame to an existing Postgres table over JDBC.

    With mode="overwrite" and truncate=True the table is emptied and refilled, so
    the DDL (primary keys, indexes, grants) survives. Without truncate, Spark
    would DROP and recreate the table and lose all of that.
    """
    try:
        url, user, password = _jdbc_connection()
        logger.info(
            "Writing DataFrame to Postgres: table=%s.%s mode=%s columns=%d",
            schema,
            table_name,
            mode,
            len(df.columns),
        )
        (
            df.write.format("jdbc")
            .option("url", url)
            .option("dbtable", f"{schema}.{table_name}")
            .option("user", user)
            .option("password", password)
            .option("driver", "org.postgresql.Driver")
            .option("batchsize", str(batch_size))
            .option("numPartitions", str(num_partitions))
            .option("truncate", str(truncate and mode == "overwrite").lower())
            .mode(mode)
            .save()
        )
    except Exception:
        logger.exception(
            "Failed to write DataFrame to Postgres: table=%s.%s mode=%s",
            schema,
            table_name,
            mode,
        )
        raise
