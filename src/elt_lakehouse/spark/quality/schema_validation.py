from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from src.elt_lakehouse.spark.utils.type_casting import resolve_spark_type


def check_validation(df: DataFrame, extracted_schema: list[dict]) -> tuple[bool, list[str]]:

    errors: list[str] = []

    expected_columns = {
        field["column_name"]: field
        for field in extracted_schema
        }

    actual_columns = {
        field.name: field
        for field in df.schema.fields
        }

    for column, contract in expected_columns.items():

        if column not in actual_columns:
            errors.append(f"{column}: missing column")
            continue

        expected_type = resolve_spark_type(contract) or contract["data_type"]
        actual_type = actual_columns[column].dataType.simpleString()

        if actual_type != expected_type:
            errors.append(
                f"{column}: expected type={expected_type}, "
                f"actual type={actual_type}"
            )

        if contract["nullable"] is False:
            has_null =(
                df.filter(F.col(column).isNull())
                .limit(1)
                .count() > 0)

            if has_null:
                errors.append(f"{column}: contains NULL values " "but nullable=False")

        minimum = contract.get("minimum")
        if minimum is not None:
            below_min = (
                df.filter(
                    (F.col(column).isNotNull()) &
                    (F.col(column) < minimum)
                    )
                .limit(1)
                .count() > 0
            )
            if below_min:
                errors.append(f"{column}: contains less than minimum = {minimum}")

        maximum = contract.get("maximum")
        if maximum is not None:
            above_max = (
                df.filter(
                    (F.col(column).isNotNull()) &
                    (F.col(column) > maximum)
                    )
                .limit(1)
                .count() > 0
                )
            if above_max:
                errors.append(
                    f"{column}: contains greater than"
                    f" maximum = {maximum}")

    return len(errors) == 0, errors
