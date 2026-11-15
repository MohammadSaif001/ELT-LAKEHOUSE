# Tests

Tests are grouped by the behavior and dependencies they exercise:

- `unit/` — fast isolated tests for generators, configuration, serving helpers,
  dashboard parsing, and PostgreSQL DDL.
- `data_quality/` — null, duplicate, referential-integrity, business-rule, and
  statistical checks.
- `integration/` — multi-stage Bronze, Silver, and Gold paths; these may need
  Spark and local data.
- `performance/` — generation and large-volume performance checks.

Run the complete suite from the repository root:

```bash
uv run pytest
```

During development, run the smallest relevant test file first. PostgreSQL DDL
tests parse the SQL files without requiring a live database; serving tests mock
the Spark/JDBC boundary.
