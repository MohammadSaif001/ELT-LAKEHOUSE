# Warehouse and serving support

This package contains PostgreSQL-facing helpers and DDL for serving the Gold
layer.

- `postgres/` contains the setup, table, and index SQL files for the `gold`
  schema, plus `configure.py` for applying them in one transaction.
- `loaders/` contains reusable loader functions and legacy warehouse loading
  paths.

The database setup command is:

```bash
uv run elt --postgres-setup
```

The direct configurator command is
`uv run python -m elt_lakehouse.warehouse.postgres.configure`. Both use an
administrator connection and are safe to rerun when the roles and schema
already exist. The current serving flow is implemented in
`src/elt_lakehouse/serving/postgres_writer.py`: Spark reads Gold Delta and
writes the configured PostgreSQL tables over JDBC, then verifies row counts.
The SQL files create the database objects; `--serve-gold` only publishes data
and does not create or alter the database schema.
