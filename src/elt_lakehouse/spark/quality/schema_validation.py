from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.elt_lakehouse.spark.utils.type_casting import resolve_spark_type


def check_validation(
    df: DataFrame, extracted_schema: list[dict]
) -> tuple[bool, list[str]]:

    errors: list[str] = []

    expected_columns = {field["column_name"]: field for field in extracted_schema}

    actual_columns = {field.name: field for field in df.schema.fields}

    nullability_checks: dict[str, str] = {}
    maximum_checks: dict[str, float | int] = {}
    minimum_checks: dict[str, float | int] = {}
    aggregate_expressions: list[F.Column] = []

    for column, contract in expected_columns.items():
        if column not in actual_columns:
            errors.append(f"{column}: missing column")
            continue

        expected_type = resolve_spark_type(contract) or contract["data_type"]
        actual_type = actual_columns[column].dataType.simpleString()

        if actual_type != expected_type:
            errors.append(
                f"{column}: expected type={expected_type}, actual type={actual_type}"
            )

        if contract["nullable"] is False:
            nullability_checks[column] = column
            aggregate_expressions.append(
                F.sum(
                    F.when(F.col(column).isNull(), 1)
                    .otherwise(0)
                    .alias(f"{column}_null_count")
                )
            )

        minimum = contract.get("minimum")
        if minimum is not None:
            minimum_checks[column] = minimum
            aggregate_expressions.append(
                F.sum(
                    F.when((F.col(column).isNotNull()) & (F.col(column) < minimum), 1)
                    .otherwise(0)
                    .alias(f"{column}_below_minimum_count")
                )
            )

        maximum = contract.get("maximum")
        if maximum is not None:
            maximum_checks[column] = maximum
            aggregate_expressions.append(
                F.sum(
                    F.when((F.col(column).isNotNull()) & (F.col(column) > maximum), 1)
                    .otherwise(0)
                    .alias(f"{column}_above_maximum_count")
                )
            )
    if aggregate_expressions:
        aggregate_results = df.agg(*aggregate_expressions).collect()[0].asDict()

        for column in nullability_checks:
            if aggregate_results.get(f"{column}_null_count", 0) > 0:
                errors.append(f"{column}: contains null values but nullable=False")

        for column, minimum in minimum_checks.items():
            if aggregate_results.get(f"{column}_below_minimum_count", 0) > 0:
                errors.append(f"{column}: contains less than minimum={minimum}")

        for column, maximum in maximum_checks.items():
            if aggregate_results.get(f"{column}_above_maximum_count", 0) > 0:
                errors.append(f"{column}: contains greater than maximum={maximum}")
    return len(errors) == 0, errors
