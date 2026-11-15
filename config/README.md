# Runtime configuration

This folder contains YAML configuration consumed by the Python, Spark, dbt,
dashboard, and serving layers. Configuration is loaded relative to the project
root by `config_loader.py`; commands should therefore be run from the
repository checkout or through the documented root-level entry points.

## Files

| File | Purpose |
| --- | --- |
| `generator_config.yaml` | Synthetic pool sizes, dataset sizes, workers, and seed settings |
| `spark_config.yaml` | Spark application, local runtime, memory, and session settings |
| `gold_dbt_config.yaml` | Gold dbt project, target, schemas, and Delta location |
| `postgress_config.yaml` | Gold PostgreSQL serving schema, table order, and JDBC settings |
| `dq_rules.yaml` | Data-quality rule configuration |
| `logging_config.yaml` | Console and rotating file logging |
| `kafka_config.yaml` | Planned Kafka producer/consumer settings |
| `airflow_config.yaml` | Planned Airflow settings |
| `minio_config.yaml` | Planned object-storage settings |
| `config_loader.py` | YAML loading and project-root path handling |

Keep secrets out of YAML. PostgreSQL and email passwords are read from
environment variables. PostgreSQL schema creation uses the administrator
variables documented in the root README and
`elt_lakehouse.warehouse.postgres.configure` module; Gold serving uses the
`POSTGRES_HOST`, `POSTGRES_DB`, and related JDBC variables. Validate changes by
running the focused tests before a full pipeline run.
