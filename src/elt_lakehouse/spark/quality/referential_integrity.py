from typing import NamedTuple

from pyspark.sql import DataFrame


class IntegrityResult(NamedTuple):
    valid_df: DataFrame
    invalid_df: DataFrame


def check_referential_integrity(
    child_df: DataFrame, parent_df: DataFrame, child_column: str, parent_column: str
) -> IntegrityResult:
    """
    Check referential integrity between two DataFrames based on specified keys.
    """
    parent_keys = parent_df.select(parent_column)

    invalid_df = child_df.join(
        parent_keys,
        child_df[child_column] == parent_keys[parent_column],
        how="left_anti",
    )

    valid_df = child_df.join(
        parent_keys,
        child_df[child_column] == parent_keys[parent_column],
        how="left_semi",
    )

    return IntegrityResult(valid_df, invalid_df)
