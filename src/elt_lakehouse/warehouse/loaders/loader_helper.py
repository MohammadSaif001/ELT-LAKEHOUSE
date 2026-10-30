"""Revenue warehouse loading helpers."""

import os

from pyspark.sql import DataFrame


def populate_postgres_table(
    df: DataFrame,
    table_name: str,
    *,
    mode: str = "overwrite",
) -> None:

    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_database = os.getenv("POSTGRES_DB", "elt_lakehouse")

    postgres_user = os.getenv("POSTGRES_USER", "postgres")

    postgres_password = os.getenv("POSTGRES_PASSWORD", "password")

    if not postgres_password:
        raise RuntimeError(
            "POSTGRES_PASSWORD environment variable is not set. \
            Please set it to the password for the Postgres user."
        )
    jdbc_url = f"jdbc:postgresql://{postgres_host}:{postgres_port}/{postgres_database}"

    (
        df.write.format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", f"gold.{table_name}")
        .option("user", postgres_user)
        .option("password", postgres_password)
        .option("driver", "org.postgresql.Driver")
        .option("batchsize", "10000")
        .mode(mode)
        .save()
    )
