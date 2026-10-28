"""Build the dbt Gold layer from the project's Silver Delta tables."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml

from config.config_loader import load_yaml

from src.elt_lakehouse.spark.common.logger import get_logger, log_duration
from src.elt_lakehouse.spark.common.paths import PROJECT_ROOT

logger = get_logger(__name__)
CONFIG = load_yaml("gold_dbt_config.yaml")
DBT_CONFIG = CONFIG["dbt"]
SPARK_CONFIG = CONFIG["spark"]
DBT_PROJECT_DIR = PROJECT_ROOT / DBT_CONFIG["project_dir"]
logger.info(
    "Gold job configuration loaded: project_dir=%s target=%s gold_schema=%s",
    DBT_PROJECT_DIR,
    DBT_CONFIG["target"],
    DBT_CONFIG["gold_schema"],
)


def _sql_literal(value: str) -> str:
    """Escape a string for use as a Spark SQL string literal."""
    return "'" + value.replace("'", "''") + "'"


def _register_silver_tables(spark) -> None:
    silver_tables = {
        table_name: PROJECT_ROOT / relative_path
        for table_name, relative_path in CONFIG["silver_tables"].items()
    }
    silver_schema = DBT_CONFIG["silver_schema"]
    gold_schema = DBT_CONFIG["gold_schema"]
    with log_duration(
        logger,
        "Registering Silver Delta tables",
        table_count=len(silver_tables),
        silver_schema=silver_schema,
        gold_schema=gold_schema,
    ):
        missing = [
            f"{table_name}: {path}"
            for table_name, path in silver_tables.items()
            if not (path / "_delta_log").is_dir()
        ]
        if missing:
            missing_text = "\n  ".join(missing)
            logger.error("Missing Silver Delta tables:\n  %s", missing_text)
            raise FileNotFoundError(
                "Required Silver Delta tables are missing. Run the Silver jobs first:\n  "
                f"{missing_text}"
            )

        gold_location = (PROJECT_ROOT / DBT_CONFIG["gold_location"]).resolve().as_uri()
        logger.info(
            "Validated Silver Delta sources: table_count=%d",
            len(silver_tables),
        )

        logger.info("Ensuring Silver schema exists: schema=%s", silver_schema)
        spark.sql(f"CREATE DATABASE IF NOT EXISTS {silver_schema}")
        logger.info(
            "Ensuring Gold schema exists: schema=%s location=%s",
            gold_schema,
            gold_location,
        )
        spark.sql(
            f"CREATE DATABASE IF NOT EXISTS {gold_schema} "
            f"LOCATION {_sql_literal(gold_location)}"
        )

        for table_name, path in silver_tables.items():
            location = path.resolve().as_uri()
            logger.info(
                "Registering Silver table: table=%s location=%s",
                f"{silver_schema}.{table_name}",
                location,
            )
            spark.sql(
                f"CREATE TABLE IF NOT EXISTS {silver_schema}.{table_name} "
                f"USING DELTA LOCATION {_sql_literal(location)}"
            )


def _profile_config() -> dict:
    profile_name = DBT_CONFIG["profile_name"]
    target = DBT_CONFIG["target"]
    logger.info(
        "Building dbt profile configuration: profile=%s target=%s adapter=%s",
        profile_name,
        target,
        DBT_CONFIG["adapter_type"],
    )
    return {
        profile_name: {
            "target": target,
            "outputs": {
                target: {
                    "type": DBT_CONFIG["adapter_type"],
                    "method": DBT_CONFIG["connection_method"],
                    "host": DBT_CONFIG["connection_host"],
                    "schema": DBT_CONFIG["gold_schema"],
                    "threads": DBT_CONFIG["threads"],
                    "server_side_parameters": SPARK_CONFIG["session_parameters"],
                }
            },
        }
    }


def _run_dbt() -> None:
    with log_duration(
        logger,
        "Running dbt Gold build",
        command=DBT_CONFIG["command"],
        target=DBT_CONFIG["target"],
        project_dir=DBT_PROJECT_DIR,
    ):
        try:
            from dbt.cli.main import dbtRunner
        except ImportError as exc:
            logger.exception("operation failed; re-raising")
            raise RuntimeError(
                "dbt-spark is required. Sync the project dependencies with `uv sync`."
            ) from exc

        with tempfile.TemporaryDirectory(
            prefix=DBT_CONFIG["temporary_profile_prefix"]
        ) as profile_dir:
            logger.info("Created temporary dbt profile directory: path=%s", profile_dir)
            profile_path = Path(profile_dir) / "profiles.yml"
            profile_path.write_text(
                yaml.safe_dump(_profile_config(), sort_keys=False), encoding="utf-8"
            )
            logger.info("Generated temporary dbt profile: path=%s", profile_path)

            environment = {
                "DBT_PROFILE_NAME": DBT_CONFIG["profile_name"],
                "DBT_FILE_FORMAT": DBT_CONFIG["file_format"],
                "DBT_SILVER_SCHEMA": DBT_CONFIG["silver_schema"],
                "GOLD_LOCATION_ROOT": (
                    PROJECT_ROOT / DBT_CONFIG["gold_location"]
                ).resolve().as_uri(),
            }
            previous_values = {key: os.environ.get(key) for key in environment}
            os.environ.update(environment)
            logger.info(
                "Applied dbt environment: variables=%s",
                ", ".join(sorted(environment)),
            )
            result = None
            try:
                logger.info(
                    "Invoking dbt: command=%s target=%s",
                    DBT_CONFIG["command"],
                    DBT_CONFIG["target"],
                )
                runner = dbtRunner()
                result = runner.invoke(
                    [
                        DBT_CONFIG["command"],
                        "--project-dir",
                        str(DBT_PROJECT_DIR),
                        "--profiles-dir",
                        profile_dir,
                        "--target",
                        DBT_CONFIG["target"],
                    ]
                )
            finally:
                for key, previous_value in previous_values.items():
                    if previous_value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = previous_value
                logger.info(
                    "Restored dbt environment: variables=%s",
                    ", ".join(sorted(environment)),
                )

        if result is None:
            raise RuntimeError("dbt invocation did not return a result.")

        logger.info(
            "dbt invocation completed: success=%s result_type=%s",
            result.success,
            type(result).__name__,
        )
        if not result.success:
            logger.error(
                "dbt Gold build failed: command=%s target=%s",
                DBT_CONFIG["command"],
                DBT_CONFIG["target"],
            )
            raise RuntimeError("dbt Gold build failed; see the dbt output above.")


def main() -> None:
    logger.info("main started")
    os.environ.setdefault("SPARK_LOCAL_IP", SPARK_CONFIG["local_ip"])
    from src.elt_lakehouse.spark.common.spark_session import create_spark_session

    logger.info(
        "Starting Gold layer build: app_name=%s local_ip=%s",
        SPARK_CONFIG["app_name"],
        os.environ["SPARK_LOCAL_IP"],
    )
    spark = create_spark_session(app_name=SPARK_CONFIG["app_name"])
    try:
        _register_silver_tables(spark)
        _run_dbt()
        logger.info("Gold layer build completed successfully.")
    except Exception:
        logger.exception("Gold layer build failed.")
        raise
    finally:
        logger.info("Stopping SparkSession.")
        spark.stop()
        logger.info("SparkSession stopped.")


if __name__ == "__main__":
    main()
