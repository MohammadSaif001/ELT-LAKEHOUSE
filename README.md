# ELT Lakehouse

A synthetic e-commerce (Olist-schema) data pipeline: generate realistic data, ingest it through Bronze → Silver Delta layers, with contract-driven schema casting and validation.

Built as a hands-on data engineering project — real Spark, real Delta Lake, real bugs found and fixed along the way.

## What problem this solves

Practicing production-grade data engineering patterns without needing a real company's data:

- Schema contracts instead of hardcoded types
- Config-driven generation instead of magic numbers
- Structured logging
- Medallion architecture (Bronze/Silver/Gold)
- Data quality and validation
- Incremental development and testing at each stage

## Architecture flow

```text
+---------------------+
|      GENERATORS     |
|     generators/     |
+---------------------+
          |
          | synthetic data, config-driven
          | -> storage/generated/*.json
          v
+---------------------+
|       BRONZE        |
|   ingestion/bronze/ |
+---------------------+
          |
          | raw ingestion
          | Delta is self-describing
          v
+---------------------+
|       SILVER        |
|     spark/silver/   |
+---------------------+
          |
          | cast to real types + validated
          | driven by contracts/*.json
          v
+---------------------+
|        GOLD         |
|    not built yet    |
+---------------------+

```

## How to use

```bash

git clone https://github.com/MohammadSaif001/ELT-LAKEHOUSE.git
cd ELT-LAKEHOUSE

uv sync
uv run python elt_pipeline.py --build-pool       # generate candidate pools (customers, products, sellers)
uv run python elt_pipeline.py --build-dataset    # generate the synthetic dataset from those pools
uv run python elt_pipeline.py --bronze-runner    # ingest generated data into Bronze Delta tables
uv run python elt_pipeline.py --silver-runner    # cast + validate Bronze into Silver Delta tables
uv run python elt_pipeline.py --run-pipeline     # all four steps, in order

```

## Status

- Done, tested: generators, Bronze ingestion
- In progress: Silver (casting + validation working; write-to-Silver step still open)
- Planned, not built: Gold, Kafka, Airflow, dbt, monitoring