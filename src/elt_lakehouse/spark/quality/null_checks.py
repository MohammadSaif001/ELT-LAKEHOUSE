from typing import NamedTuple

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)


class NullCheckResult(NamedTuple):
    clean_df: DataFrame
    quarantine_df: DataFrame


def check_nulls(df: DataFrame, extracted_schema: list[dict]) -> NullCheckResult:

    null_condition = F.lit(False)
    non_nullable_columns: list[str] = []

    for field in extracted_schema:
        column = field["column_name"]
        nullable = field["nullable"]

        if column not in df.columns:
            continue

        if nullable is False:
            non_nullable_columns.append(column)

            column_null_condition = F.col(column).isNull()
            null_condition = null_condition | column_null_condition

        elif nullable is True:
            null_count = df.filter(F.col(column).isNull()).limit(1).count()

            if null_count > 0:
                logger.warning(
                    f"Column '{column}' is nullable and contains null values. This is allowed by the contract."
                )

    if not non_nullable_columns:
        logger.info(
            "No non-nullable columns found. NULL handling check completed successfully."
        )

        empty_quarantine_df = df.limit(0)

        return NullCheckResult(df, empty_quarantine_df)

    quarantine_df = df.filter(null_condition)

    clean_df = df.filter(~null_condition)

    if quarantine_df.count() > 0:
        logger.error(
            "NULL validation failed for non-nullable columns: %s",
            non_nullable_columns,
        )
    else:
        logger.info(
            "NULL validation passed for non-nullable columns: %s",
            non_nullable_columns,
        )

    return NullCheckResult(clean_df, quarantine_df)
