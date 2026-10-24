"""Build the dbt Gold layer from the project's Silver Delta tables."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml

from config.config_loader import load_yaml
from src.elt_lakehouse.spark.common.paths import PROJECT_ROOT

CONFIG = load_yaml("gold_dbt_config.yaml")
DBT_CONFIG = CONFIG["dbt"]
SPARK_CONFIG = CONFIG["spark"]
DBT_PROJECT_DIR = PROJECT_ROOT / DBT_CONFIG["project_dir"]


def _sql_literal(value: str) -> str:
    """Escape a string for use as a Spark SQL string literal."""
    return "'" + value.replace("'", "''") + "'"


def _register_silver_tables(spark) -> None:
    silver_tables = {
        table_name: PROJECT_ROOT / relative_path
        for table_name, relative_path in CONFIG["silver_tables"].items()
    }
    missing = [
        f"{table_name}: {path}"
        for table_name, path in silver_tables.items()
        if not (path / "_delta_log").is_dir()
    ]
    if missing:
        missing_text = "\n  ".join(missing)
        raise FileNotFoundError(
            "Required Silver Delta tables are missing. Run the Silver jobs first:\n  "
            f"{missing_text}"
        )

    silver_schema = DBT_CONFIG["silver_schema"]
    gold_schema = DBT_CONFIG["gold_schema"]
    gold_location = (PROJECT_ROOT / DBT_CONFIG["gold_location"]).resolve().as_uri()

    spark.sql(f"CREATE DATABASE IF NOT EXISTS {silver_schema}")
    spark.sql(
        f"CREATE DATABASE IF NOT EXISTS {gold_schema} "
        f"LOCATION {_sql_literal(gold_location)}"
    )

    for table_name, path in silver_tables.items():
        location = path.resolve().as_uri()
        spark.sql(
            f"CREATE TABLE IF NOT EXISTS {silver_schema}.{table_name} "
            f"USING DELTA LOCATION {_sql_literal(location)}"
        )


def _profile_config() -> dict:
    profile_name = DBT_CONFIG["profile_name"]
    target = DBT_CONFIG["target"]
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
    try:
        from dbt.cli.main import dbtRunner
    except ImportError as exc:
        raise RuntimeError(
            "dbt-spark is required. Sync the project dependencies with `uv sync`."
        ) from exc

    with tempfile.TemporaryDirectory(
        prefix=DBT_CONFIG["temporary_profile_prefix"]
    ) as profile_dir:
        profile_path = Path(profile_dir) / "profiles.yml"
        profile_path.write_text(
            yaml.safe_dump(_profile_config(), sort_keys=False), encoding="utf-8"
        )

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
        try:
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

        if not result.success:
            raise RuntimeError("dbt Gold build failed; see the dbt output above.")


def main() -> None:
    os.environ.setdefault("SPARK_LOCAL_IP", SPARK_CONFIG["local_ip"])
    from src.elt_lakehouse.spark.common.spark_session import create_spark_session

    spark = create_spark_session(app_name=SPARK_CONFIG["app_name"])
    try:
        _register_silver_tables(spark)
        _run_dbt()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
