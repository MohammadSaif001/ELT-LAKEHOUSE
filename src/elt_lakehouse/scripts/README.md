# Utility scripts

Scripts in this folder are small command-line entry points for operations that
are also exposed by the main pipeline.

`run_gold_dbt.py` is a compatibility entry point for the Gold build. It adds
the repository root to `sys.path`, imports
`elt_lakehouse.spark.jobs.gold_job.main`, and delegates to that job:

```bash
uv run python -m elt_lakehouse.scripts.run_gold_dbt
```

Prefer `uv run elt --gold-runner` when using the main
orchestration interface. Keep scripts thin; stage logic belongs under
`src/elt_lakehouse/`.
