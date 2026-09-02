from pyspark.sql import DataFrame
from pyspark.sql.functions import col, to_timestamp

SPARK_TYPE_MAP = {
    "string": "string",
    "int": "int",
    "number": "double",
    "boolean": "boolean",
    "date": "date",
    "timestamp": "timestamp",
    "float": "float",
}


def cast_using_contract(df: DataFrame, extracted_schema: list[dict]) -> DataFrame:

    casted = df

    for field in extracted_schema:
        column = field["column_name"]
        if column not in casted.columns:
            continue
        if "date-time" in field["column_name"]:
            if field.get("format") == "date-time":
                casted = casted.withColumn(column, to_timestamp(col(column)))
                continue
            continue

        data_type = field["data_type"]

        spark_type = SPARK_TYPE_MAP.get(data_type)

        if spark_type is None:
            continue

        casted = casted.withColumn(column, col(column).cast(spark_type))

    return casted
