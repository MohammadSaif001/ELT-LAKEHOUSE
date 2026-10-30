"""Unit tests for Gold -> PostgreSQL serving (no Spark or Postgres needed)."""

import sys
import types
from unittest.mock import MagicMock

import pytest

try:  # use the real pyspark when installed, a stub otherwise
    import pyspark.sql  # noqa: F401
except ImportError:
    pyspark = types.ModuleType("pyspark")
    sql = types.ModuleType("pyspark.sql")
    sql.DataFrame = object
    sql.SparkSession = object
    pyspark.sql = sql
    sys.modules.update({"pyspark": pyspark, "pyspark.sql": sql})

try:
    import py4j.protocol  # noqa: F401
except ImportError:
    py4j = types.ModuleType("py4j")
    protocol = types.ModuleType("py4j.protocol")
    protocol.Py4JError = Exception
    py4j.protocol = protocol
    sys.modules.update({"py4j": py4j, "py4j.protocol": protocol})

from src.elt_lakehouse.ingestion.core import writer  # noqa: E402
from src.elt_lakehouse.serving import postgres_writer as pw  # noqa: E402


class _Recorder:
    """Stands in for df.write: records .option() calls and the final mode/save."""

    def __init__(self):
        self.options, self.saved_mode = {}, None

    def format(self, _):
        return self

    def option(self, key, value):
        self.options[key] = value
        return self

    def mode(self, mode):
        self.saved_mode = mode
        return self

    def save(self):
        return None


def _df(rows=5):
    df = MagicMock()
    df.columns = ["a", "b"]
    df.count.return_value = rows
    df.write = _Recorder()
    return df


def test_write_postgres_truncates_on_overwrite(monkeypatch):
    monkeypatch.setenv("POSTGRES_PASSWORD", "x")
    df = _df()
    writer.write_postgres(df, "dim_customer", mode="overwrite", schema="gold")
    opts = df.write.options
    assert opts["truncate"] == "true"  # keeps PKs, indexes and grants
    assert opts["dbtable"] == "gold.dim_customer"
    assert "rewriteBatchedInserts=true" in opts["url"]
    assert opts["numPartitions"] == "4"


def test_write_postgres_append_does_not_truncate(monkeypatch):
    monkeypatch.setenv("POSTGRES_PASSWORD", "x")
    df = _df()
    writer.write_postgres(df, "t", mode="append")
    assert df.write.options["truncate"] == "false"


def test_write_postgres_requires_password(monkeypatch):
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        writer.write_postgres(_df(), "t")


@pytest.fixture
def fake_io(monkeypatch):
    calls = []
    monkeypatch.setattr(pw, "read_delta", lambda spark, path: calls.append(("read", path)) or _df(5))
    monkeypatch.setattr(pw, "write_postgres", lambda df, table, **kw: calls.append(("write", table, kw)))
    monkeypatch.setattr(pw, "postgres_row_count", lambda spark, table, schema: 5)
    monkeypatch.setattr(pw, "missing_tables", lambda spark, tables, schema: [])
    return calls


def test_publish_table_reads_delta_and_verifies(fake_io):
    assert pw.publish_table(MagicMock(), "dim_seller") == 5
    assert fake_io[0][0] == "read" and fake_io[0][1].endswith("dim_seller")
    assert fake_io[1][2]["truncate"] is True


def test_publish_table_row_count_mismatch_raises(fake_io, monkeypatch):
    monkeypatch.setattr(pw, "postgres_row_count", lambda *a, **k: 4)
    with pytest.raises(RuntimeError, match="mismatch"):
        pw.publish_table(MagicMock(), "dim_seller")


def test_publish_gold_dimensions_before_facts(fake_io):
    result = pw.publish_gold(MagicMock())
    written = [c[1] for c in fake_io if c[0] == "write"]
    assert written == list(result)
    assert written.index("dim_customer") < written.index("fact_orders")
    assert len(written) == 9


def test_publish_gold_attempts_all_then_reports_failures(fake_io, monkeypatch):
    def flaky(df, table, **kw):
        if table == "dim_date":
            raise ConnectionError("db down")
        fake_io.append(("write", table, kw))

    monkeypatch.setattr(pw, "write_postgres", flaky)
    with pytest.raises(RuntimeError, match="dim_date"):
        pw.publish_gold(MagicMock())
    assert len([c for c in fake_io if c[0] == "write"]) == 8  # the rest still ran


def test_publish_gold_only_and_unknown(fake_io):
    assert list(pw.publish_gold(MagicMock(), only=["fact_orders"])) == ["fact_orders"]
    with pytest.raises(ValueError):
        pw.publish_gold(MagicMock(), only=["nope"])


def test_publish_gold_fails_before_writing_when_tables_missing(fake_io, monkeypatch):
    monkeypatch.setattr(
        pw, "missing_tables", lambda spark, tables, schema: ["fact_orders"]
    )
    with pytest.raises(RuntimeError, match="fact_orders.*create_tables|missing"):
        pw.publish_gold(MagicMock())
    assert [c for c in fake_io if c[0] == "write"] == []  # nothing was written


def test_preflight_checks_only_selected_tables(fake_io, monkeypatch):
    seen = {}
    monkeypatch.setattr(
        pw,
        "missing_tables",
        lambda spark, tables, schema: seen.setdefault("tables", tables) and [],
    )
    pw.publish_gold(MagicMock(), only=["dim_seller"])
    assert seen["tables"] == ["dim_seller"]


def test_missing_tables_reports_absent(monkeypatch):
    monkeypatch.setenv("POSTGRES_PASSWORD", "x")

    class _Reader:
        def format(self, _): return self
        def option(self, *_): return self
        def load(self): return self
        def collect(self): return [{"table_name": "dim_date"}, {"table_name": "dim_seller"}]

    spark = MagicMock()
    spark.read = _Reader()
    assert pw.missing_tables(spark, ["dim_date", "dim_seller", "fact_orders"], "gold") == ["fact_orders"]
