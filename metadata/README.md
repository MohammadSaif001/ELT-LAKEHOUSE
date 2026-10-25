# Entity metadata

`entities.yaml` is the static control file for the local Bronze and Silver
pipeline. The Python code loads and validates it at runtime. It contains
entity registrations, JSON contract references, enabled stages, deduplication
rules, allowlisted handler names, stage input and output paths, and
referential-integrity relationships.

## Editing the manifest

- Use the canonical entity IDs already used by the Silver processors, such as
  `geolocation` and `order_items`.
- Keep field definitions, types, and nullability in `contracts/*.json`; use
  `contract` only to reference the file.
- `deduplication.policy` currently supports `drop_duplicates` and `none`.
  `drop_duplicates` uses Spark `dropDuplicates`; it does not mean “keep latest”.
- `bronze.handler` and `silver.handler` must name functions registered in the
  corresponding job's Python allowlist. Metadata cannot import arbitrary code.
- `bronze.source` must stay under `storage/generated/`, and `bronze.target`
  under `storage/bronze/`.
- `silver.source` must stay under `storage/bronze/`, and `silver.target`
  under `storage/silver/`.
- Referential-integrity quarantine paths must remain under
  `storage/silver/quarantine/` and point to declared entities and contract
  columns.
- The `version` field is the manifest format version. A structural format
  change must update the loader and version handling together.

The loader rejects unsupported versions, missing contracts, invalid keys,
unknown stages, invalid output or quarantine paths, and unknown handler names
when the stage builds its execution plan.

Checkpoint files, pipeline state, and watermarks are mutable runtime state;
they do not belong in this static manifest.
