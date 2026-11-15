# Data contracts

The JSON files in this folder define the expected input shape for each Olist
dataset. Bronze and Silver jobs use them for schema resolution, type casting,
required-field checks, and contract validation.

`schema_utils.py` provides shared loading and validation helpers. Contract names
are referenced by [`metadata/entities.yaml`](../metadata/entities.yaml), so
renaming a contract requires updating that manifest.

## Editing rules

- Keep entity names aligned with the IDs in `metadata/entities.yaml`.
- Treat field names and types as pipeline interfaces; update the readers and
  tests when changing them.
- Use the contract for structure and nullability, not for stage paths or job
  handler configuration.
- Run the data-quality and contract-focused tests after changes.
