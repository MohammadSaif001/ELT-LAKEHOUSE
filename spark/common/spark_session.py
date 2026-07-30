from pyspark.sql import SparkSession
from spark.common.logger import get_logger
from config.config_loader import load_yaml

CONFIG = load_yaml("spark_config.yaml")

logger   = get_logger("spark.common.spark_session")


#===============================
# Create Spark Session
#===============================

def create_spark_session(app_name: str | None = None) -> SparkSession:
    """Create and return a Spark session configured for Delta Lake."""
    try:
        config = load_yaml("spark_config.yaml")
        spark_config = config["spark"]

        resolved_app_name = app_name or spark_config.get("app_name", "Modern Lakehouse")

        # Prefer structured keys under `sql` in config (`sql.shuffle_partitions`, `sql.timezone`).
        sql_config = spark_config.get("sql", {})
        shuffle_partitions = sql_config.get("shuffle_partitions", 200)
        session_timezone = sql_config.get("timezone", "UTC")

        logger.info(
            "Creating SparkSession: app_name=%s, master=%s",
            resolved_app_name,
            spark_config.get("master", "local[*]"),
        )

        builder = (
            SparkSession.builder
            .appName(resolved_app_name)
            .master(spark_config.get("master", "local[*]"))
            .config(
                "spark.sql.extensions",
                "io.delta.sql.DeltaSparkSessionExtension",
            )
            .config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            )
            .config("spark.sql.shuffle.partitions", shuffle_partitions)
            .config("spark.sql.session.timeZone", session_timezone)
        )

        
        # Attempt to use the Python `delta` helper if available; otherwise
        # fall back to adding the Delta Spark package via Maven coordinates.
        try:
            from delta import configure_spark_with_delta_pip as configure_delta
        except Exception:
            configure_delta = None

        if configure_delta:
            spark = configure_delta(builder).getOrCreate()
        else:
            # Default Maven coordinate for Delta Spark (adjust if needed)
            delta_maven = spark_config.get("delta", {}).get(
                "maven_coord", "io.delta:delta-spark_4.1_2.13:4.3.1"
            )
            builder = builder.config("spark.jars.packages", delta_maven)
            spark = builder.getOrCreate()

        logger.info(
            "SparkSession created: app_name=%s, spark_version=%s, user=%s",
            spark.sparkContext.appName,
            spark.version,
            spark.sparkContext.sparkUser(),
        )
        return spark

    except Exception:
        logger.exception("Failed to create SparkSession with Delta Lake support")
        raise