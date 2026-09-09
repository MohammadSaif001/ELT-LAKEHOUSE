from pyspark.sql import DataFrame
from pyspark.sql.functions import col, to_timestamp

SPARK_TYPE_MAP = {
    "string": "string",
    "integer": "int",
    "number": "double",
    "boolean": "boolean",
}


def resolve_spark_type(field: dict) -> str | None:
    if field.get("format") == "date-time":
        return "timestamp"
    if field.get("format") == "float":
        return "float"
    return SPARK_TYPE_MAP.get(field["data_type"])


def cast_using_contract(df: DataFrame, extracted_schema: list[dict]) -> DataFrame:

    casted = df

    for field in extracted_schema:
        column = field["column_name"]
        if column not in casted.columns:
            continue

        spark_type = resolve_spark_type(field)
        if spark_type is None:
            continue
        if spark_type == "timestamp":
            casted = casted.withColumn(column, to_timestamp(col(column)))
        else:
            casted = casted.withColumn(column, col(column).cast(spark_type))

    return casted
