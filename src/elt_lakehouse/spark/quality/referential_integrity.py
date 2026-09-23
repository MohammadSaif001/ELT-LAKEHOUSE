from typing import NamedTuple

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


class IntegrityResult(NamedTuple):
    valid_df: DataFrame
    invalid_df: DataFrame


def check_referential_integrity(
    child_df: DataFrame, parent_df: DataFrame, child_column: str, parent_column: str
) -> IntegrityResult:
    """Check referential integrity between two DataFrames based on specified keys.

    Uses a single ``left`` join and splits the result by whether the parent key
    matched, rather than running separate ``left_anti`` and ``left_semi`` joins.
    This halves the number of shuffle-join plans (from 2 to 1 per check).

    Args:
        child_df: The child DataFrame whose foreign key is being validated.
        parent_df: The parent DataFrame containing the primary key.
        child_column: Name of the foreign key column in ``child_df``.
        parent_column: Name of the primary key column in ``parent_df``.

    Returns:
        An ``IntegrityResult`` named tuple with:
        - ``valid_df``: rows in ``child_df`` whose key exists in ``parent_df``
          (equivalent to a ``left_semi`` join).
        - ``invalid_df``: rows in ``child_df`` whose key is absent in ``parent_df``
          (equivalent to a ``left_anti`` join).
    """

    sentinel = "__ref_key__"

    parent_keys = parent_df.select(F.col(parent_column).alias(sentinel)).distinct()

    joined = child_df.join(
        parent_keys,
        child_df[child_column] == F.col(sentinel),
        how="left",
    )

    valid_df = joined.filter(F.col(sentinel).isNotNull()).drop(sentinel)

    invalid_df = joined.filter(F.col(sentinel).isNull()).drop(sentinel)

    return IntegrityResult(valid_df, invalid_df)
