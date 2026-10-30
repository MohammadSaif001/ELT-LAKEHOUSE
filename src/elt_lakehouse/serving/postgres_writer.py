"""Publish finished Gold Delta tables to PostgreSQL (the serving layer).

Flow per table: read Gold Delta -> write to Postgres over JDBC -> compare row counts.
Gold is built in Spark; Postgres only receives the finished tables. Nothing here
touches Delta, so a failed publish can be retried without rebuilding Gold.
"""

from pathlib import Path

from config.config_loader import load_yaml
from src.elt_lakehouse.ingestion.core.reader import read_delta
from src.elt_lakehouse.ingestion.core.writer import _jdbc_connection, write_postgres
from src.elt_lakehouse.spark.common.logger import get_logger, kv, log_duration
from src.elt_lakehouse.spark.common.paths import GOLD_DIR

logger = get_logger(__name__)


def _config() -> dict:
    return load_yaml("postgress_config.yaml")


def gold_table_order(config: dict | None = None) -> list[str]:
    """Dimensions first, then facts, in the order given in the config."""
    tables = (config or _config())["tables"]
    return [*tables["dimensions"].values(), *tables["facts"].values()]


def postgres_row_count(spark, table_name: str, schema: str) -> int:
    url, user, password = _jdbc_connection()
    row = (
        spark.read.format("jdbc")
        .option("url", url)
        .option("user", user)
        .option("password", password)
        .option("driver", "org.postgresql.Driver")
        .option("query", f"SELECT COUNT(*) AS n FROM {schema}.{table_name}")
        .load()
        .collect()[0]
    )
    return int(row["n"])


def missing_tables(spark, tables: list[str], schema: str) -> list[str]:
    """Return the configured tables that do not exist in Postgres yet."""
    url, user, password = _jdbc_connection()
    rows = (
        spark.read.format("jdbc")
        .option("url", url)
        .option("user", user)
        .option("password", password)
        .option("driver", "org.postgresql.Driver")
        .option(
            "query",
            "SELECT tablename AS table_name FROM pg_catalog.pg_tables "
            f"WHERE schemaname = '{schema}'",
        )
        .load()
        .collect()
    )
    existing = {row["table_name"] for row in rows}
    return [table for table in tables if table not in existing]


def publish_table(
    spark,
    table_name: str,
    *,
    schema: str = "gold",
    gold_dir: Path = GOLD_DIR,
    batch_size: int = 10_000,
    num_partitions: int = 4,
    verify: bool = True,
) -> int:
    """Publish one Gold table to Postgres and return its row count."""
    delta_path = Path(gold_dir) / table_name
    with log_duration(logger, "postgres publish", table=f"{schema}.{table_name}"):
        df = read_delta(spark, str(delta_path))  # read_delta, NOT read_parquet
        source_rows = df.count()
        write_postgres(
            df,
            table_name,
            mode="overwrite",
            schema=schema,
            truncate=True,
            batch_size=batch_size,
            num_partitions=num_partitions,
        )
        if verify:
            target_rows = postgres_row_count(spark, table_name, schema)
            if target_rows != source_rows:
                raise RuntimeError(
                    f"Row count mismatch for {schema}.{table_name}: "
                    f"delta={source_rows} postgres={target_rows}"
                )
        logger.info(
            "Postgres table published: %s",
            kv(table=f"{schema}.{table_name}", rows=source_rows),
        )
    return source_rows


def publish_gold(spark, only: list[str] | None = None) -> dict[str, int]:
    """Publish every configured Gold table (or just ``only``). Returns rows per table.

    Every table is attempted; if any fail, one error listing them is raised at
    the end, so a rerun with ``only=[...]`` can retry just the failed ones.
    """
    config = _config()
    jdbc = config.get("jdbc", {})
    schema = config.get("schema", "gold")
    tables = gold_table_order(config)
    if only:
        unknown = set(only) - set(tables)
        if unknown:
            raise ValueError(f"Unknown Gold tables: {sorted(unknown)}")
        tables = [t for t in tables if t in only]

    # Spark would silently CREATE a missing table without keys, indexes or grants,
    # so fail early and tell the user to run the DDL first.
    absent = missing_tables(spark, tables, schema)
    if absent:
        raise RuntimeError(
            f"Postgres tables missing in schema '{schema}': {', '.join(absent)}. "
            "Run setup.sql, create_tables.sql, and create_indexes.sql in "
            "src/elt_lakehouse/warehouse/postgres/ first."
        )

    published: dict[str, int] = {}
    failed: list[str] = []
    with log_duration(logger, "postgres gold publish", tables=len(tables)):
        for table in tables:
            try:
                published[table] = publish_table(
                    spark,
                    table,
                    schema=schema,
                    batch_size=jdbc.get("batch_size", 10_000),
                    num_partitions=jdbc.get("num_partitions", 4),
                )
            except Exception:
                logger.exception("Postgres publish failed: table=%s.%s", schema, table)
                failed.append(table)
    if failed:
        raise RuntimeError(f"Postgres publish failed for: {', '.join(failed)}")
    return published
