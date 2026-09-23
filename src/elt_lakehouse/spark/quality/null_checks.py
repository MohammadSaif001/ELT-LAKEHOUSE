from typing import NamedTuple

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)


class NullCheckResult(NamedTuple):
    clean_df: DataFrame
    quarantine_df: DataFrame
    has_quarantine: bool


def check_nulls(df: DataFrame, extracted_schema: list[dict]) -> NullCheckResult:
    """Separate rows with nulls in non-nullable columns from clean rows.

    Args:
        df: Input DataFrame to check.
        extracted_schema: List of field dicts from the contract, each containing
            at least ``column_name`` and ``nullable`` keys.

    Returns:
        A ``NullCheckResult`` with:
        - ``clean_df``: rows where all non-nullable columns are non-null.
        - ``quarantine_df``: rows that violate at least one non-nullable column.
        - ``has_quarantine``: ``True`` if the quarantine DataFrame is non-empty.
          This avoids a second Spark action in the caller.
    """

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

    if not non_nullable_columns:
        logger.info(
            "No non-nullable columns found. NULL handling check completed successfully."
        )

        empty_quarantine_df = df.limit(0)

        return NullCheckResult(df, empty_quarantine_df, has_quarantine=False)

    quarantine_df = df.filter(null_condition)

    clean_df = df.filter(~null_condition)
    quarantine_exists = quarantine_df.limit(1).count() > 0
    if quarantine_exists:
        logger.error(
            "NULL validation failed for non-nullable columns: %s",
            non_nullable_columns,
        )
    else:
        logger.info(
            "NULL validation passed for non-nullable columns: %s",
            non_nullable_columns,
        )

    return NullCheckResult(clean_df, quarantine_df, has_quarantine=quarantine_exists)
