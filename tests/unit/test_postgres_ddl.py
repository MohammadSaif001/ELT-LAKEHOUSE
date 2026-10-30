"""The Postgres DDL must stay in step with the dbt Gold models and the serving config."""

import re
from pathlib import Path

import pytest
import yaml

pglast = pytest.importorskip("pglast")
sqlglot = pytest.importorskip("sqlglot")

ROOT = Path(__file__).resolve().parents[2]
PG_DIR = ROOT / "src/elt_lakehouse/warehouse/postgres"
MODELS = ROOT / "dbt_gold/models"
CONFIG = yaml.safe_load((ROOT / "config/postgress_config.yaml").read_text())


def _ddl_tables() -> dict[str, list[str]]:
    tables: dict[str, list[str]] = {}
    for stmt in pglast.parse_sql((PG_DIR / "create_tables.sql").read_text()):
        create = stmt.stmt
        name = create.relation.relname
        tables[name] = [
            col.colname for col in create.tableElts if type(col).__name__ == "ColumnDef"
        ]
    return tables


def _model_columns(model: str) -> list[str]:
    path = next(MODELS.rglob(f"{model}.sql"))
    sql = path.read_text()
    sql = re.sub(r"\{\{\s*config\(.*?\)\s*\}\}", "", sql, flags=re.DOTALL)
    sql = re.sub(
        r"\{\{\s*(?:source|ref)\((?:'[^']*',\s*)?'([^']*)'\)\s*\}\}", r"\1", sql
    )
    return sqlglot.parse_one(sql, read="spark").named_selects


def _configured_tables() -> list[str]:
    tables = CONFIG["tables"]
    return [*tables["dimensions"].values(), *tables["facts"].values()]


def test_all_sql_files_parse_as_postgres():
    for sql_file in PG_DIR.glob("*.sql"):
        assert pglast.parse_sql(sql_file.read_text()), sql_file.name


def test_ddl_covers_exactly_the_configured_tables():
    assert set(_ddl_tables()) == set(_configured_tables())


@pytest.mark.parametrize("table", _configured_tables())
def test_ddl_columns_match_dbt_model(table):
    assert _ddl_tables()[table] == _model_columns(table)


def test_every_table_has_a_primary_key():
    for stmt in pglast.parse_sql((PG_DIR / "create_tables.sql").read_text()):
        constraints = [
            c
            for elt in stmt.stmt.tableElts
            for c in (getattr(elt, "constraints", None) or [])
            if c.contype.name == "CONSTR_PRIMARY"
        ] + [
            elt
            for elt in stmt.stmt.tableElts
            if type(elt).__name__ == "Constraint"
            and elt.contype.name == "CONSTR_PRIMARY"
        ]
        assert constraints, stmt.stmt.relation.relname


def test_indexes_only_reference_existing_tables():
    tables = _ddl_tables()
    for stmt in pglast.parse_sql((PG_DIR / "create_indexes.sql").read_text()):
        index = stmt.stmt
        assert index.relation.relname in tables
        columns = {p.name for p in index.indexParams}
        assert columns <= set(tables[index.relation.relname])
