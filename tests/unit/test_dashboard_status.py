from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

from fastapi.testclient import TestClient
from dashboard import app as dashboard_app
from dashboard.services import dbt_reader, health_service, status_service
from dashboard.services.dbt_reader import DbtRunSummary, DbtTestResult


def _write_log(project_root, lines):
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "application.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _log_line(timestamp, level, logger, message):
    return f"{timestamp} | {level} | {logger} | {message}"


def test_incomplete_latest_run_does_not_inherit_old_success_or_output(tmp_path):
    old = datetime.now() - timedelta(hours=2)
    current = datetime.now()
    old_start = old.strftime("%Y-%m-%d %H:%M:%S")
    old_finish = (old + timedelta(seconds=14)).strftime("%Y-%m-%d %H:%M:%S")
    latest_start = current.strftime("%Y-%m-%d %H:%M:%S")
    _write_log(tmp_path, [
        _log_line(old_start, "INFO", "__main__", "Starting ELT pipeline..."),
        _log_line(old_finish, "INFO", "__main__", "ELT pipeline completed successfully in 14.00 seconds."),
        _log_line(latest_start, "INFO", "__main__", "Starting ELT pipeline..."),
    ])
    output = tmp_path / "storage/generated/generated_customers_data.json"
    output.parent.mkdir(parents=True)
    output.write_text("{}", encoding="utf-8")

    overview = status_service.get_overview(tmp_path)
    health = health_service.build_health_report(overview)

    assert overview.latest_run_status == status_service.STATUS_RUNNING
    assert overview.last_run_started == latest_start
    assert overview.last_run_finished is None
    assert overview.last_run_duration is None
    assert overview.last_successful_run == old_finish
    assert overview.stages[0].status == status_service.STATUS_UNKNOWN
    assert next(check for check in health.checks if check.key == "last_run").status == health_service.HEALTH_WARN


def test_stage_completion_and_duration_come_from_stage_log(tmp_path):
    started = datetime.now() - timedelta(seconds=5)
    completed = datetime.now()
    _write_log(tmp_path, [
        _log_line(started.strftime("%Y-%m-%d %H:%M:%S"), "INFO", "__main__", "Starting ELT pipeline..."),
        _log_line(completed.strftime("%Y-%m-%d %H:%M:%S"), "INFO",
                  "src.elt_lakehouse.spark.jobs.dataset_job",
                  "Dataset generation completed successfully in duration_s=4.75"),
        _log_line(completed.strftime("%Y-%m-%d %H:%M:%S"), "INFO", "__main__",
                  "ELT pipeline completed successfully in 5.00 seconds."),
    ])

    overview = status_service.get_overview(tmp_path)
    dataset = next(stage for stage in overview.stages if stage.stage.key == "dataset_generation")

    assert overview.latest_run_status == status_service.STATUS_SUCCESS
    assert overview.last_run_duration is not None
    assert dataset.status == status_service.STATUS_SUCCESS
    assert dataset.duration == "4.75s"


def test_stage_failure_is_not_hidden_by_existing_output(tmp_path):
    started = datetime.now() - timedelta(seconds=2)
    failed = datetime.now()
    _write_log(tmp_path, [
        _log_line(started.strftime("%Y-%m-%d %H:%M:%S"), "INFO", "__main__", "Starting ELT pipeline..."),
        _log_line(failed.strftime("%Y-%m-%d %H:%M:%S"), "ERROR",
                  "src.elt_lakehouse.spark.jobs.silver_job", "Silver layer processing failed."),
        _log_line(failed.strftime("%Y-%m-%d %H:%M:%S"), "ERROR", "__main__",
                  "Pipeline failed with a critical error."),
    ])
    silver_output = tmp_path / "storage" / "silver" / "customers_silver"
    silver_output.mkdir(parents=True)
    (silver_output / "part-000.parquet").write_bytes(b"existing")

    overview = status_service.get_overview(tmp_path)
    silver = next(stage for stage in overview.stages if stage.stage.key == "silver_transformation")

    assert overview.latest_run_status == status_service.STATUS_FAILED
    assert silver.status == status_service.STATUS_FAILED


def test_dashboard_routes_render_with_unknown_metrics(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard_app, "PROJECT_ROOT", tmp_path)
    state_dir = tmp_path / "metadata" / "pipeline_state"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text(
        '{"password": "do-not-render", "state": "local"}', encoding="utf-8"
    )
    dbt_target = tmp_path / "dbt_gold" / "target"
    dbt_target.mkdir(parents=True)
    (dbt_target / "run_results.json").write_text(json.dumps({
        "metadata": {"generated_at": "2026-10-25T12:00:00Z"},
        "results": [
            {"unique_id": "test.project.sample_check.abcdef123456", "status": "pass", "failures": 0},
            {"unique_id": "test.project.failed_check.c35b36c6fa", "status": "fail", "failures": 3},
            {"unique_id": "model.project.dim_customer", "status": "success", "execution_time": 1.25},
        ],
    }), encoding="utf-8")
    client = TestClient(dashboard_app.app)

    for route in ("/", "/pipeline-run", "/data-quality", "/storage-health", "/technical-details", "/gold-layer", "/stage/pool_generation"):
        response = client.get(route)
        assert response.status_code == 200, route
        assert response.headers["Cache-Control"] == "no-store"
    assert client.get("/stage/not-a-stage").status_code == 404
    stylesheet = client.get("/static/css/style.css")
    assert stylesheet.status_code == 200
    assert "report.css" in stylesheet.text
    health_response = client.get("/api/health")
    assert health_response.status_code == 503
    assert health_response.json()["dbt_tests"]["failed"] == 1

    home = client.get("/").text
    assert "Pipeline overview" in home
    assert "PostgreSQL writer exists" in home
    assert "dbt tests" in home
    assert "failed_check" in home
    assert "Latest run timeline" in home
    assert "Data flow status" in home
    assert "/static/css/style.css?v=4" in home
    storage = client.get("/storage-health").text
    assert "[REDACTED]" in storage
    assert "do-not-render" not in storage
    quality = client.get("/data-quality").text
    assert "failed_check" in quality
    assert "3" in quality


def test_dbt_run_results_reader_reports_tests_without_exposing_environment(tmp_path):
    target = tmp_path / "dbt_gold" / "target"
    target.mkdir(parents=True)
    (target / "run_results.json").write_text(json.dumps({
        "metadata": {
            "generated_at": "2026-10-25T12:00:00Z",
            "invocation_started_at": "2026-10-25T11:59:00Z",
            "env": {"DB_PASSWORD": "secret-value"},
        },
        "results": [
            {"unique_id": "test.project.good_check.abcdef123456", "status": "pass", "failures": 0},
            {"unique_id": "test.project.bad_check.c35b36c6fa", "status": "fail", "failures": 3},
            {"unique_id": "test.project.skipped_check.0123456789ab", "status": "skipped"},
            {"unique_id": "model.project.dim_customer", "status": "success", "execution_time": 1.25},
        ],
    }), encoding="utf-8")

    summary = dbt_reader.read_run_results(tmp_path)

    assert summary is not None
    assert (summary.tests_total, summary.tests_passed, summary.tests_failed, summary.tests_skipped) == (3, 1, 1, 1)
    assert summary.failed_tests[0].name == "bad_check"
    assert summary.failed_tests[0].failures == 3
    assert summary.models[0].name == "dim_customer"
    assert not hasattr(summary, "env")


def test_old_dbt_failures_are_not_attributed_to_a_newer_execution():
    started = datetime.now()
    overview = status_service.PipelineOverview(
        overall_status=status_service.STATUS_RUNNING,
        stages=[], storage_layers=[], recent_runs=[], log_file_exists=True,
        pipeline_state_raw=None, watermark_raw=None, checkpoint_raw=None,
        last_run_started=started.strftime("%Y-%m-%d %H:%M:%S"),
        latest_run_status=status_service.STATUS_RUNNING,
    )
    old_report = DbtRunSummary(
        generated_at=(datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        invocation_started_at=None,
        tests_total=1, tests_passed=0, tests_failed=1, tests_errored=0,
        tests_warned=0, tests_skipped=0,
        failed_tests=[DbtTestResult("stale_check", "fail", 5)],
    )

    check = health_service._check_dbt_tests(overview, old_report)

    assert check.status == health_service.HEALTH_UNKNOWN
    assert "predates" in check.message


def test_identified_completion_does_not_pair_with_different_run_start(tmp_path):
    _write_log(tmp_path, [
        _log_line(
            "2026-10-26 00:00:00", "INFO", "__main__",
            "Starting ELT pipeline... execution_id=run-new",
        ),
        _log_line(
            "2026-10-26 00:00:01", "INFO", "__main__",
            "Starting ELT pipeline... execution_id=run-old",
        ),
        _log_line(
            "2026-10-26 00:00:02", "INFO", "__main__",
            "ELT pipeline completed successfully in 2.00 seconds. execution_id=run-new",
        ),
    ])

    overview = status_service.get_overview(tmp_path)

    assert overview.latest_run_status == status_service.STATUS_SUCCESS
    assert overview.last_run_started == "2026-10-26 00:00:00"
    assert overview.last_run_duration == "2.00s"


def test_out_of_order_completion_timestamp_has_no_duration(tmp_path):
    _write_log(tmp_path, [
        _log_line("2026-10-26 00:00:10", "INFO", "__main__", "Starting ELT pipeline..."),
        _log_line(
            "2026-10-26 00:00:05", "INFO", "__main__",
            "ELT pipeline completed successfully in 5.00 seconds.",
        ),
    ])

    overview = status_service.get_overview(tmp_path)

    assert overview.latest_run_status == status_service.STATUS_SUCCESS
    assert overview.last_run_duration is None


def test_homepage_does_not_show_health_checks_as_data_quality_checks(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard_app, "PROJECT_ROOT", tmp_path)
    client = TestClient(dashboard_app.app)

    response = client.get("/")

    assert response.status_code == 200
    assert "dbt tests" in response.text
    assert ">N/A<" in response.text


def test_dashboard_redacts_secret_values_from_logs(tmp_path, monkeypatch):
    _write_log(tmp_path, [
        _log_line(
            "2026-10-26 01:00:00", "INFO", "test",
            "password=secret-pass token='secret-token' "
            "connection_string=postgresql://user:secret-db@localhost/db",
        ),
    ])
    monkeypatch.setattr(dashboard_app, "PROJECT_ROOT", tmp_path)

    response = TestClient(dashboard_app.app).get("/technical-details")

    assert response.status_code == 200
    assert "secret-pass" not in response.text
    assert "secret-token" not in response.text
    assert "secret-db" not in response.text
    assert "[REDACTED]" in response.text
