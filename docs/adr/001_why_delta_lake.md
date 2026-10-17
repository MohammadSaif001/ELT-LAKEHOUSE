# ADR 001 — Why Delta Lake

| Field       | Value                          |
|-------------|-------------------------------|
| **Status**  | Accepted                       |
| **Date**    | 2026-09-01                     |
| **Author**  | Mohammad Saif                  |

---

## Context

The ELT-Lakehouse project processes synthetic e-commerce data through a
**Bronze → Silver → Gold** Medallion pipeline using Apache Spark. We needed a
table format for the Silver and Gold layers that could satisfy:

1. **ACID transactions** — concurrent Spark writes must not corrupt table state.
2. **Schema enforcement** — each entity (customers, products, orders, …) has a
   strict contract; bad rows must be rejected, not silently accepted.
3. **Time-travel / audit** — quarantine re-processing requires reading a
   specific historical snapshot.
4. **Upsert / merge support** — the Silver layer deduplicates incoming rows;
   `MERGE INTO` is the cleanest way to express this.
5. **Local development** — the pipeline must run fully offline (no cloud
   object store) using `local[8]` Spark master.

---

## Decision

We use **Delta Lake** (via `delta-spark`) as the table format for the Silver
and Gold layers.

```
Bronze  → raw Parquet files (append-only, no schema enforcement)
Silver  → Delta tables     (schema-enforced, deduplicated, quarantine output)
Gold    → Delta tables     (aggregated, business-ready)
```

---

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Plain Parquet** | Zero dependencies, fastest reads | No ACID, no upserts, no time-travel |
| **Apache Iceberg** | Feature-rich, cloud-native | Heavier local setup; PySpark 4 integration less mature at decision time |
| **Apache Hudi** | Strong upsert story | Complex configuration; smaller community |
| **Delta Lake** ✅ | ACID, schema enforcement, `MERGE`, time-travel, first-class PySpark 4 support, active OSS community | Requires `delta-spark` dependency and `DeltaSparkSessionExtension` |

---

## Consequences

### Positive
- Schema contracts are enforced at write time — bad data is routed to quarantine
  tables automatically by the validation decorator.
- `MERGE INTO` in the Gold layer enables idempotent re-runs.
- `DESCRIBE HISTORY` gives a full audit trail for every Silver/Gold table.
- The `_delta_log/` transaction log means partial writes never leave tables in
  a corrupt state.

### Negative / Trade-offs
- SparkSession must be initialised with `DeltaSparkSessionExtension` and
  `DeltaCatalog` — slightly more complex session setup.
- Delta table directories accumulate `_delta_log/` JSON files; periodic
  `VACUUM` is required in production to manage storage.
- Local reads via `read_delta()` are slightly slower than raw Parquet for the
  Bronze layer, which is why Bronze stays as plain Parquet.

---

## Implementation Notes

- Session configuration lives in [`config/spark_config.yaml`](../../config/spark_config.yaml).
- `DeltaSparkSessionExtension` and `io.delta.sql.DeltaSparkSessionExtension`
  are applied in the shared `create_spark_session()` helper.
- Silver writes use `write_delta(df, path, mode="overwrite")`.
- Quarantine writes use `mode="append"` so historical bad rows are preserved.

