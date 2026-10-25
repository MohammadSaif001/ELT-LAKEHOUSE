# ELT Lakehouse

An end-to-end data engineering project for generating, ingesting, validating,
and monitoring synthetic e-commerce data. The pipeline uses an Olist-style
domain model and stores data in Delta Lake using a Bronze → Silver → Gold
medallion layout.

## Project status

| Area | Status | Notes |
| --- | --- | --- |
| Synthetic data generation | Implemented | Config-driven pools and datasets for customers, products, sellers, orders, payments, reviews, and geolocation |
| Bronze layer | Implemented | Spark ingestion writes the generated datasets to Delta tables |
| Silver layer | Implemented | Contract-based casting, validation, referential-integrity checks, Delta outputs, and quarantine tables |
| Data quality | Implemented | Null, duplicate, freshness, schema, business-rule, and referential-integrity checks |
| Incremental processing | Available in code | CDC, merge, and watermark helpers are present and can be extended for production workloads |
| Monitoring dashboard | Implemented | Read-only FastAPI dashboard for pipeline status, data quality, storage health, logs, and `/api/health` |
| Kafka ingestion | In development | Producer, consumer, topic-management, and Kafka-to-Bronze modules are present but require a running Kafka environment |
| Airflow orchestration | In development | DAGs, callbacks, alerts, and custom operators are present under `airflow/` |
| dbt Gold modeling | Implemented | Gold dimensions, facts, sources, and tests are defined under `dbt_gold/` and run through the Spark/dbt Gold job |
| Gold and warehouse loading | Available in code | Gold Delta outputs and a PostgreSQL writer are available; deployment-specific warehouse configuration and end-to-end validation remain |

## Architecture

```text
                         config/*.yaml
                              |
                              v
+-------------------+   synthetic data    +----------------------+
| Generators        | ------------------> | storage/generated/   |
| pools + datasets  |                     +----------+-----------+
+-------------------+                                |
                                                    v
                                          +----------------------+
                                          | Bronze Delta tables  |
                                          | storage/bronze/      |
                                          +----------+-----------+
                                                     |
                                  contracts/*.json   |
                                                     v
                                          +----------------------+
                                          | Silver Delta tables  |
                                          | storage/silver/      |
                                          | + quarantine tables  |
                                          +----------+-----------+
                                                     |
                                                     v
                                          +----------------------+
                                          | Gold / warehouse     |
                                          | dbt + PostgreSQL     |
                                          | available in code    |
                                          +----------------------+
```

The pipeline currently covers eight related datasets:

- customers
- geolocation
- orders
- order items
- payments
- reviews
- products
- sellers

Schema contracts in [`contracts/`](contracts/) define the expected data shape.
Runtime configuration, generator distributions, and service settings live in
[`config/`](config/).

## Requirements

- Python 3.10 or newer
- Java and Apache Spark-compatible runtime for Spark jobs
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency management

The Python package dependencies are declared in
[`pyproject.toml`](pyproject.toml) and locked in [`uv.lock`](uv.lock).

## Quick start

```bash
git clone https://github.com/MohammadSaif001/ELT-LAKEHOUSE.git
cd ELT-LAKEHOUSE

uv sync
```

The project uses the public Olist dataset from Kaggle for profiling and source
data. To download it and build the profiling metadata, configure Kaggle API
credentials on your machine (see the
[Kaggle API setup guide](https://www.kaggle.com/docs/api)), then run:

```bash
uv run python elt_pipeline.py --setup
```

The setup step reuses a complete local dataset. The raw CSV files and generated
profiles are local artifacts and are excluded from Git. After setup, generate
synthetic data and run each layer independently:

```bash
uv run python elt_pipeline.py --build-pool
uv run python elt_pipeline.py --build-dataset
uv run python elt_pipeline.py --bronze-runner
uv run python elt_pipeline.py --silver-runner
```

Or run setup, profiling, pool generation, dataset generation, Bronze, and
Silver in sequence:

```bash
uv run python elt_pipeline.py --run-pipeline
```

`--run-pipeline` requires Kaggle credentials only when the complete raw dataset
is not already present locally. You can also combine stage flags; they always
run in dependency order.

Build the Gold layer after Silver has completed:

```bash
uv run python scripts/run_gold_dbt.py
```

The Gold job registers the Silver Delta tables with Spark, creates a temporary
dbt profile, and writes Gold Delta tables under `storage/gold/`. It does not
require a user-managed `~/.dbt/profiles.yml`.

The current generator configuration creates pools of up to 1,000,000
customers, 100,000 products, and 200,000 sellers, with a configured dataset
volume of up to 800,000 orders. Adjust
[`config/generator_config.yaml`](config/generator_config.yaml) before running
large workloads on a machine with limited resources.

## Testing

Run the test suite with:

```bash
uv run pytest
```

Focused suites are organized under:

- [`tests/unit/`](tests/unit/) — generators, configuration, and Spark utilities
- [`tests/data_quality/`](tests/data_quality/) — data-quality and business rules
- [`tests/integration/`](tests/integration/) — pipeline and Kafka integration paths
- [`tests/performance/`](tests/performance/) — generation and large-volume checks

## Repository layout

```text
config/       Runtime, generator, Spark, and service configuration
contracts/    JSON schema contracts and schema utilities
dashboard/    Read-only FastAPI monitoring dashboard
dbt_gold/     dbt Gold models, sources, macros, and tests
docs/         Architecture, ADRs, lineage, plans, and runbooks
src/          Generators, ingestion, Spark jobs, quality checks, and loaders
storage/      Generated data and Bronze/Silver/Gold Delta output locations
tests/        Unit, data-quality, integration, and performance tests
airflow/      Airflow DAGs, callbacks, alerts, and custom operators
docker/       Service configuration for local infrastructure
monitoring/   Prometheus and Grafana configuration
```

## Development notes

- The [Gold layer catalog](docs/catalog.md) documents Gold model grains,
  keys, sources, published columns, and validation rules.
- Spark jobs use structured logging and memory-monitoring helpers.
- Invalid records identified during Silver referential-integrity checks are
  written to `storage/silver/quarantine/`.
- The monitoring dashboard is read-only; it reports pipeline state but does not
  start jobs or write data.
- Generated data and pipeline state are local runtime artifacts; review the
  configured paths before running high-volume jobs.
- Kafka and Airflow workflows should be treated as development integrations
  until their local infrastructure and end-to-end tests are enabled.
- The dbt Gold job and PostgreSQL writer are available in code, but production
  deployment still requires environment-specific configuration and validation.
