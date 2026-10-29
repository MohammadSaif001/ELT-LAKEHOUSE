"""Tests for dashboard log parsing and stage/job status detection."""

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from dashboard.services import log_reader, pipeline_registry, status_service

J = "src.elt_lakehouse.spark.jobs."
BRONZE = {
    "customers": "Customer", "geolocations": "Geolocation", "orders": "Order",
    "order items": "Order items", "payments": "Payment", "reviews": "Reviews",
    "sellers": "Seller", "products": "Product",
}


class LogBuilder:
    def __init__(self):
        self.t = datetime.now() - timedelta(minutes=30)
        self.lines: list[str] = []

    def add(self, logger_name, message, level="INFO", seconds=1):
        self.t += timedelta(seconds=seconds)
        self.lines.append(f"{self.t:%Y-%m-%d %H:%M:%S} | {level} | {logger_name} | {message}")

    def full_run(self):
        self.add("__main__", "Starting ELT pipeline...")
        self.add(J + "pool_job", "Starting pool generation...")
        for n in ("customers", "products", "customer locations", "sellers"):
            self.add(J + "pool_job", f"Generating pool: {n}")
        self.add(J + "pool_job", "Pool generation completed successfully in duration_s=114.79")
        for n in ("customers", "geolocations", "sellers", "products", "orders",
                  "order items", "payments", "reviews"):
            self.add(J + "dataset_job", f"Generating dataset:{n}")
        self.add(J + "dataset_job", "Dataset generation completed successfully in duration_s=40.00")
        self.add(J + "bronze_job", "Starting bronze ingestion.")
        for name, label in BRONZE.items():
            self.add(J + "bronze_job", f"Ingesting dataset:{name}")
            self.add("src.elt_lakehouse.ingestion.bronze.x",
                     f"Starting {label.lower()} ingestion: input_path=a, output_path=b")
            self.add("src.elt_lakehouse.ingestion.bronze.x",
                     f"{label} ingestion completed successfully: output_path=b")
        self.add(J + "bronze_job", "All ingestion functions completed successfully in duration_s=80.10")
        self.add(J + "silver_job", "Starting silver layer processing...")
        self.add(J + "silver_job", "All data validations completed successfully in duration_s=60.00")
        self.add(J + "gold_job", "Running dbt Gold build started command=build")
        self.add(J + "gold_job", "Running dbt Gold build completed duration_s=60.5 command=build")
        self.add(J + "gold_job", "Gold layer build completed successfully in duration_s=61.20")
        self.add("__main__", "ELT pipeline completed successfully in 300.00 seconds.")

    def write(self, root: Path) -> Path:
        (root / "logs").mkdir(parents=True, exist_ok=True)
        (root / "logs" / "application.log").write_text("\n".join(self.lines) + "\n")
        return root


@pytest.fixture(autouse=True)
def _quiet_and_fresh():
    logging.disable(logging.CRITICAL)
    getattr(log_reader, "_CACHE", {}).clear()
    yield
    logging.disable(logging.NOTSET)


def _statuses(overview):
    return {s.stage.key: s for s in overview.stages}


def test_full_successful_run_marks_every_job_success(tmp_path):
    b = LogBuilder(); b.full_run(); b.write(tmp_path)
    overview = status_service.get_overview(tmp_path)
    assert overview.latest_run_status == status_service.STATUS_SUCCESS
    bad = [(s.stage.key, j.job.key, j.status) for s in overview.stages for j in s.jobs
           if j.status != status_service.STATUS_SUCCESS]
    assert bad == []


def test_bronze_registry_covers_all_ingested_datasets(tmp_path):
    keys = {j.key for s in pipeline_registry.PIPELINE_STAGES
            if s.key == "bronze_ingestion" for j in s.jobs}
    assert keys == {"customers", "geolocation", "orders", "order_items",
                    "payments", "reviews", "sellers", "products"}


def test_gold_stage_reports_a_duration(tmp_path):
    b = LogBuilder(); b.full_run(); b.write(tmp_path)
    gold = _statuses(status_service.get_overview(tmp_path))["gold_transformation"]
    assert gold.status == status_service.STATUS_SUCCESS
    assert gold.duration == "61.20s"


def test_log_duration_completion_line_is_recognised():
    assert status_service._message_is_completion(
        "Running dbt Gold build completed duration_s=60.5 command=build")
    assert not status_service._message_is_completion("Generating pool: customers")


def test_partial_rerun_keeps_earlier_stage_results(tmp_path):
    b = LogBuilder(); b.full_run()
    b.add("__main__", "Starting ELT pipeline...", seconds=30)
    b.add(J + "gold_job", "Gold layer build completed successfully in duration_s=4.00")
    b.add("__main__", "ELT pipeline completed successfully in 4.00 seconds.")
    b.write(tmp_path)
    stages = _statuses(status_service.get_overview(tmp_path))
    assert {k: v.status for k, v in stages.items()} == {
        k: status_service.STATUS_SUCCESS for k in stages}


def test_failed_stage_is_reported_failed(tmp_path):
    b = LogBuilder()
    b.add("__main__", "Starting ELT pipeline...")
    b.add(J + "bronze_job", "Starting bronze ingestion.")
    b.add(J + "bronze_job", "Ingestion failed.", level="ERROR")
    b.add("__main__", "Pipeline failed with a critical error.", level="ERROR")
    b.write(tmp_path)
    overview = status_service.get_overview(tmp_path)
    assert overview.latest_run_status == status_service.STATUS_FAILED
    assert _statuses(overview)["bronze_ingestion"].status == status_service.STATUS_FAILED


def test_field_values_do_not_keep_trailing_commas(tmp_path):
    fields = log_reader._parse_fields(
        "Order dataset generated: records=8000, path=storage/o.parquet, duration_s=2.50")
    assert fields == {"records": "8000", "path": "storage/o.parquet", "duration_s": "2.50"}


def test_quoted_and_escaped_values():
    fields = log_reader._parse_fields(r'name="two words" note="say \"hi\"" p="C:\Users\x"')
    assert fields["name"] == "two words"
    assert fields["note"] == 'say "hi"'
    assert fields["p"] == r"C:\Users\x"


def test_table_like_continuation_line_is_not_a_new_event(tmp_path):
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "application.log").write_text(
        "2026-10-29 04:00:01 | ERROR | x | step failed\n"
        "Traceback (most recent call last):\n"
        "| col_a | col_b | col_c | col_d |\n"
        "2026-10-29 04:00:02 | INFO | x | next\n")
    events = log_reader.read_events(tmp_path)
    assert [e.message.splitlines()[0] for e in events] == ["step failed", "next"]
    assert "| col_a |" in events[0].message


def test_dashboard_logger_lines_are_ignored(tmp_path):
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "application.log").write_text(
        "2026-10-29 04:00:01 | INFO | dashboard.services.storage_reader | inspect started\n"
        "continuation of a dashboard record\n"
        "2026-10-29 04:00:02 | INFO | src.elt_lakehouse.spark.jobs.silver_job | Silver ok\n")
    events = log_reader.read_events(tmp_path)
    assert [e.logger_name for e in events] == ["src.elt_lakehouse.spark.jobs.silver_job"]


def test_events_are_cached_until_file_changes(tmp_path):
    b = LogBuilder(); b.full_run(); b.write(tmp_path)
    first = log_reader.read_events(tmp_path)
    assert log_reader.read_events(tmp_path) is first
    with (tmp_path / "logs" / "application.log").open("a") as fh:
        fh.write("2030-01-01 00:00:00 | INFO | x | extra\n")
    assert log_reader.read_events(tmp_path) is not first


def test_registry_strings_exist_in_source():
    """Every dashboard match string must be producible by a real log message."""
    src = "\n".join(p.read_text(errors="ignore")
                    for p in Path("src").rglob("*.py")).lower()
    missing = []
    for stage in pipeline_registry.PIPELINE_STAGES:
        needles = [stage.completion_match] + [j.log_match for j in stage.jobs]
        for needle in needles:
            # templated messages ("Generating pool: %s") are matched by prefix
            probe = re.split(r"[:]", needle.lower())[0] if ":" in needle else needle.lower()
            if probe not in src:
                missing.append(needle)
    assert missing == []
