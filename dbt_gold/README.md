# Gold dbt project

This is the dbt project for the Gold layer. It transforms registered Silver
Delta tables into dimensional and fact models under `storage/gold/`.

The Spark Gold job registers the Silver tables, creates a temporary dbt profile,
and invokes this project. Run it from the repository root with:

```bash
uv run elt --gold-runner
```

The compatibility command below runs the same Gold job:

```bash
uv run python -m elt_lakehouse.scripts.run_gold_dbt
```

## Layout

- `models/` contains staging, dimensions, facts, and model metadata.
- `tests/` contains dbt data-quality and relationship tests.
- `macros/` contains reusable SQL macros.
- `target/` and `logs/` are generated dbt artifacts and should not be edited
  manually.

Silver Delta tables must exist before the Gold build starts. The model grains,
keys, and source relationships are documented in [`docs/catalog.md`](../docs/catalog.md).
