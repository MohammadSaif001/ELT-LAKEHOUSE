import os

from pyspark.sql import SparkSession

from config.config_loader import load_yaml
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import PROJECT_ROOT

os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")

logger = get_logger("spark.common.spark_session")

spark_tmp_dir = os.path.expanduser("~/.spark_tmp")
os.makedirs(spark_tmp_dir, exist_ok=True)

# ===============================
# Create Spark Session
# ===============================


def create_spark_session(app_name: str | None = None) -> SparkSession:
    """Create and return a Spark session configured for Delta Lake."""
    try:
        CONFIG = load_yaml("spark_config.yaml")
        spark_config = CONFIG["spark"]

        resolved_app_name = app_name or spark_config.get("app_name", "Modern Lakehouse")

        sql_config = spark_config.get("sql", {})
        shuffle_partitions = sql_config.get("shuffle_partitions", 200)
        session_timezone = sql_config.get("timezone", "UTC")

        logger.info(
            "Creating SparkSession: app_name=%s, master=%s",
            resolved_app_name,
            spark_config.get("master", "local[*]"),
        )

        builder = (
            SparkSession.builder.appName(resolved_app_name)
            .master(spark_config.get("master", "local[8]"))
            .config("spark.driver.memory", spark_config["memory"].get("driver", "4g"))
            .config(
                "spark.executor.memory", spark_config["memory"].get("executor", "4g")
            )
            .config(
                "spark.sql.extensions",
                "io.delta.sql.DeltaSparkSessionExtension",
            )
            .config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            )
            .config(
                "spark.sql.files.maxPartitionBytes",
                spark_config["sql"].get("maxPartitionBytes", "67108864"),
            )
            .config("spark.sql.shuffle.partitions", shuffle_partitions)
            .config("spark.sql.session.timeZone", session_timezone)
            .config("spark.driver.host", "127.0.0.1")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.local.dir", spark_tmp_dir)
            .config("spark.jars.ivy", str(PROJECT_ROOT / ".ivy2"))
        )

        try:
            from delta import configure_spark_with_delta_pip as configure_delta
        except ImportError:
            configure_delta = None

        # JDBC driver for publishing Gold to PostgreSQL (downloaded once via Ivy).
        jdbc_package = load_yaml("postgress_config.yaml").get("jdbc", {}).get("package")
        extra_packages = [jdbc_package] if jdbc_package else []

        if configure_delta:
            spark = configure_delta(
                builder, extra_packages=extra_packages
            ).getOrCreate()
        else:
            # Default Maven coordinate for Delta Spark
            delta_maven = spark_config.get("delta", {}).get(
                "maven_coord", "io.delta:delta-spark_4.1_2.13:4.3.1"
            )
            builder = builder.config(
                "spark.jars.packages", ",".join([delta_maven, *extra_packages])
            )
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
