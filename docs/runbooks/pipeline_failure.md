# Runbook — Pipeline Failure Recovery

| Field        | Value                           |
|--------------|---------------------------------|
| **Severity** | P1 (pipeline completely stopped) |
| **Owner**    | Mohammad Saif                   |
| **Updated**  | 2026-10-16                      |

---

## Overview

This runbook covers diagnosing and recovering from failures in the
ELT-Lakehouse batch pipeline. The pipeline runs in four sequential stages,
followed by an optional Gold build and warehouse publishing step:

```
Pool Generation → Dataset Generation → Bronze Ingestion → Silver Processing
                                                        ↘ Gold → PostgreSQL
```

A failure in any stage aborts all subsequent stages. Add
`--send-report` when an email report is required on success or failure.

---

## Quick Triage

```bash
# Re-run the full batch pipeline and send a report
uv run python elt_pipeline.py --run-pipeline --send-report

# Run only a specific stage (useful for partial re-runs)
uv run python elt_pipeline.py --build-pool
uv run python elt_pipeline.py --build-dataset
uv run python elt_pipeline.py --bronze-runner
uv run python elt_pipeline.py --silver-runner
uv run python elt_pipeline.py --gold-runner
uv run python elt_pipeline.py --serve-gold
```

Inspect the logs while diagnosing a failure:

```bash
tail -f logs/application.log
tail -f logs/dashboard.log  # dashboard service diagnostics only
```

`logs/application.log` contains pipeline and application events used by the
dashboard for run status. Dashboard service messages are isolated in
`logs/dashboard.log` and are not part of pipeline status evaluation.

---

## Stage 1 — Pool Generation Failures

### Symptom
```
ERROR | src.elt_lakehouse.spark.jobs.pool_job | An error occurred during pool generation.
FileNotFoundError: Failed to open local file 'metadata/pools/customer_pool.parquet'
```

### Cause
The `metadata/pools/` directory does not exist. This happens on a **fresh
clone** or after `metadata/` is cleaned up.

### Fix
```bash
mkdir -p metadata/pools
uv run python elt_pipeline.py --build-pool
```

### Prevention
The pool job auto-creates `metadata/pools/` on startup. If the directory is
missing, it means `pool_job.py`'s directory-creation guard was bypassed. Check
[`src/elt_lakehouse/spark/jobs/pool_job.py`](../../src/elt_lakehouse/spark/jobs/pool_job.py)
for the `Path(POOLS_DIR).mkdir(parents=True, exist_ok=True)` call.

---

## Stage 2 — Dataset Generation Failures

### Symptom
```
ERROR | src.elt_lakehouse.spark.jobs.dataset_job | Dataset generation failed
KeyError: 'customer_id'
```

### Cause A — Pool files missing
Dataset generation loads pool Parquet files (`customer_pool.parquet`,
`product_pool.parquet`, etc.) at runtime. If Stage 1 was skipped or failed,
these files don't exist.

**Fix**: Run Stage 1 first, then retry Stage 2.

### Cause B — Pool schema mismatch
A code change altered the pool schema without re-generating the pools.

**Fix**:
```bash
rm -f metadata/pools/*.parquet
uv run python elt_pipeline.py --build-pool
uv run python elt_pipeline.py --build-dataset
```

### Cause C — Output directory missing
```
FileNotFoundError: storage/generated/
```

**Fix**:
```bash
mkdir -p storage/generated
```

---

## Stage 3 — Bronze Ingestion Failures

### Symptom
```
ERROR | elt_lakehouse.spark.jobs.bronze_job | Schema validation failed for orders
AnalysisException: cannot resolve 'seller_id' given input columns
```

### Cause A — Generated Parquet schema drift
The Bronze ingestion scripts (`customers.py`, `orders.py`, etc.)
have a hardcoded `INPUT_PATH` pointing to `storage/generated/*.parquet`.
If the generator added/removed columns, the Bronze schema contract is broken.

**Fix**:
1. Check the generator output schema:
   ```python
   import pyarrow.parquet as pq

   print(pq.read_schema("storage/generated/generated_orders_data.parquet"))
   ```
2. Update the Bronze script's schema contract or the generator to match.

### Cause B — SparkSession not shared
Bronze and Silver share a SparkSession (passed through `elt_pipeline.py`). If
Bronze is run standalone with `--bronze-runner`, it creates its own session. This
is expected behaviour.

### Cause C — Delta table already locked
```
ConcurrentAppendException: Files were added to the root of the table
```

**Fix**:
```bash
# Remove the Delta table and re-run Bronze to recreate it
rm -rf storage/bronze/orders_delta/
uv run python elt_pipeline.py --bronze-runner
```

---

## Stage 4 — Silver Processing Failures

### Symptom A — Null check failure
```
ERROR | silver_job | Quarantine threshold exceeded for customers
```

This is **expected behaviour**, not a bug. More than the allowed percentage of
rows are null in a required column. Check the generated data distribution via
`config/generator_config.yaml`.

### Symptom B — Referential integrity failure (all rows quarantined)
```
WARNING | referential_integrity | 0 valid rows after integrity check: orders → customers
```

**Cause**: The Silver `customers` table has not been written yet, but `orders`
tries to join against it.

**Fix**: Ensure Silver processes entities in dependency order. Check
[`silver_job.py`](../../src/elt_lakehouse/spark/jobs/silver_job.py) — parents
(`customers`, `products`, `sellers`) must be written before children
(`orders`, `order_items`, `payments`, `reviews`).

### Symptom C — Out of memory
```
java.lang.OutOfMemoryError: GC overhead limit exceeded
```

**Fix**:
```bash
# Increase driver memory in config/spark_config.yaml
# driver_memory: 4g → 8g
# Then clear Spark's local temp directory:
rm -rf /tmp/spark-*
uv run python elt_pipeline.py --silver-runner
```

## Stage 5 — Gold Build Failures

Gold is built separately after Silver completes:

```bash
uv run python scripts/run_gold_dbt.py
```

### Symptom — Missing Silver Delta table

The Gold job reports the Silver table paths that are missing. Run the Bronze
and Silver stages first, then retry the Gold build:

```bash
uv run python elt_pipeline.py --bronze-runner
uv run python elt_pipeline.py --silver-runner
uv run python scripts/run_gold_dbt.py
```

### Symptom — dbt profile or adapter error

The Gold job creates a temporary profile automatically. Do not create or edit
`~/.dbt/profiles.yml` for this project. Run `uv sync` if the dbt-spark adapter
is unavailable, then retry the command.

### Symptom D — Delta transaction conflict
```
ConcurrentModificationException: Transaction has encountered too many conflicts
```

**Fix**: Ensure no other Spark process is writing to the same Delta tables.
Check for lingering `java` processes:
```bash
ps aux | grep java
kill <pid>  # if any stale Spark driver is found
```

---

## Full Reset (Nuclear Option)

If the pipeline state is completely corrupted:

```bash
# Remove all generated data, pools, and Delta tables
rm -rf metadata/pools/
rm -rf metadata/pools/
rm -rf storage/generated/ storage/bronze/ storage/silver/ storage/gold/

# Re-run from scratch
uv run python elt_pipeline.py --run-pipeline --send-report
```

> [!WARNING]
> This deletes all Bronze and Silver Delta history. Use only in development.

---

## Checking Test Suite Health

Before investigating pipeline issues, verify the test suite passes:

```bash
uv run pytest tests/ -x -q
# Expected: 36 passed
```

If tests fail, fix them before debugging the pipeline — a test failure usually
points directly to the broken component.

---

## Log Locations

| What | Where |
|------|-------|
| Pipeline stdout | Terminal / `--send-report` email |
| Spark driver logs | `spark-warehouse/` (local mode) |
| Delta transaction log | `storage/<layer>/<table>/_delta_log/` |
| Pool files | `metadata/pools/*.parquet` |
| Generated data | `storage/generated/*.parquet` |
