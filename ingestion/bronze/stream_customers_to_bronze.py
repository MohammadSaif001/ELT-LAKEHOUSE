from pyspark.sql.types import *
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.appName("StreamCustomersToBronze").master("local[*]").getOrCreate()

print(f"Spark version: {spark.version}")
print(f"Spark session created with app name: {spark.sparkContext.appName}")
print(f"Spark master: {spark.sparkContext.master}")
print(f"Spark UI available at: {spark.sparkContext.uiWebUrl}")
print(f"Spark session started at: {spark.sparkContext.startTime}")
print(f"Spark session ID: {spark.sparkContext.applicationId}")
print(f"Spark session user: {spark.sparkContext.sparkUser()}")