# ELT Lakehouse Python package

This package contains the reusable implementation behind the `elt` CLI.
The package entry point selects an action; modules here implement generation, ingestion,
Spark transformations, quality checks, serving, and shared utilities.

## Main areas

- `generators/` — creates pools and synthetic Parquet datasets.
- `ingestion/` — reads source files and writes Bronze Delta data; Kafka and
  bootstrap paths are separate adapters.
- `spark/` — Spark sessions, jobs, Silver transformations, quality checks, and
  the Gold dbt runner.
- `serving/` — publishes completed Gold Delta tables to PostgreSQL.
- `warehouse/` — reusable loaders and PostgreSQL DDL for the serving layer.
- `tracking/` — reserved for run, batch, and execution metadata management.

Shared paths and logging helpers live under `spark/common/`. Keep orchestration
in `elt_pipeline.py` or job modules, and keep reusable stage logic inside this
package.
