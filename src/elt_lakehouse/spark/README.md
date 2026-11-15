# Spark jobs and transformations

This package owns the Spark execution layer:

- `jobs/` exposes pipeline stages such as dataset generation, Bronze, Silver,
  and Gold.
- `silver/` transforms Bronze DataFrames into Silver outputs.
- `quality/` implements schema, null, duplicate, freshness, business-rule, and
  referential-integrity checks.
- `common/` provides Spark sessions, paths, logging, schema loading, and shared
  helpers.
- `incremental/` contains planned watermark, CDC, and merge components.
- `utils/` contains memory monitoring and type-casting utilities.

Bronze and Silver share a Spark session during `--run-pipeline`. Silver writes
invalid relationship rows to `storage/silver/quarantine/` and writes validated
outputs to `storage/silver/`. Gold registers Silver Delta tables before
invoking the dbt project.
