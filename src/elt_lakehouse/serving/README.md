# Gold serving

This package publishes completed Gold Delta tables to PostgreSQL for analysts
and downstream applications.

`postgres_writer.py` determines the configured dimension-before-fact order,
reads each table from `storage/gold/`, writes it over Spark JDBC, and compares
source and target row counts. It does not build Gold models and does not create
the production PostgreSQL DDL; those responsibilities belong to the Spark Gold
job and `warehouse/postgres/`.

Run the serving stage from the repository root:

```bash
uv run elt --serve-gold
```

PostgreSQL serving connection values come from `POSTGRES_HOST`,
`POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`.
Create the roles, schema, tables, and indexes first with:

```bash
uv run elt --postgres-setup
```

The configurator uses an administrator connection, while `--serve-gold` uses
the serving/loader connection.
