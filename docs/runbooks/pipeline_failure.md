# Runbook — Pipeline Failure Recovery

| Field        | Value                           |
|--------------|---------------------------------|
| **Severity** | P1 (pipeline completely stopped) |
| **Owner**    | Mohammad Saif                   |
| **Updated**  | 2026-10-16                      |

---

## Overview

This runbook covers diagnosing and recovering from failures in the
ELT-Lakehouse batch pipeline. The pipeline runs in four sequential stages:

```
Pool Generation → Dataset Generation → Bronze Ingestion → Silver Processing
```

A failure in any stage aborts all subsequent stages. An email report is sent
automatically on both success and failure.

---

## Quick Triage

```bash
# Re-run the full pipeline with verbose output
uv run python3 -m elt_pipeline --run-pipeline --send-report

# Run only a specific stage (useful for partial re-runs)
uv run python3 -m elt_pipeline --run-pool
uv run python3 -m elt_pipeline --run-dataset
uv run python3 -m elt_pipeline --run-bronze
uv run python3 -m elt_pipeline --run-silver
```

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
uv run python3 -m elt_pipeline --run-pool
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
uv run python3 -m elt_pipeline --run-pool
uv run python3 -m elt_pipeline --run-dataset
```

### Cause C — Output directory missing
```
FileNotFoundError: metadata/generated/
```

**Fix**:
```bash
mkdir -p metadata/generated
```

---

## Stage 3 — Bronze Ingestion Failures

### Symptom
```
ERROR | elt_lakehouse.spark.jobs.bronze_job | Schema validation failed for orders
AnalysisException: cannot resolve 'seller_id' given input columns
```

### Cause A — Generated Parquet schema drift
The Bronze ingestion scripts (`customers_bronze.py`, `orders_bronze.py`, etc.)
have a hardcoded `INPUT_PATH` pointing to `metadata/generated/*.parquet`.
If the generator added/removed columns, the Bronze schema contract is broken.

**Fix**:
1. Check the generator output schema:
   ```python
   import pyarrow.parquet as pq
   print(pq.read_schema("metadata/generated/orders.parquet"))
   ```
2. Update the Bronze script's schema contract or the generator to match.

### Cause B — SparkSession not shared
Bronze and Silver share a SparkSession (passed through `elt_pipeline.py`). If
Bronze is run standalone with `--run-bronze`, it creates its own session. This
is expected behaviour.

### Cause C — Delta table already locked
```
ConcurrentAppendException: Files were added to the root of the table
```

**Fix**:
```bash
# Remove the Delta table and re-run Bronze to recreate it
rm -rf delta/bronze/orders/
uv run python3 -m elt_pipeline --run-bronze
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
uv run python3 -m elt_pipeline --run-silver
```

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
rm -rf metadata/generated/
rm -rf delta/

# Re-run from scratch
uv run python3 -m elt_pipeline --run-pipeline --send-report
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
| Delta transaction log | `delta/<layer>/<table>/_delta_log/` |
| Pool files | `metadata/pools/*.parquet` |
| Generated data | `metadata/generated/*.parquet` |

