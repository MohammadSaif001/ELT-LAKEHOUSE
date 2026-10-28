from __future__ import annotations

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

from dataclasses import dataclass
from datetime import datetime, timedelta

from dashboard.services.status_service import (
    _parse_ts,
    STATUS_FAILED,
    STATUS_RUNNING,
    STATUS_SUCCESS,
    PipelineOverview,
)
from dashboard.services.dbt_reader import DbtRunSummary

HEALTH_OK = "OK"
HEALTH_WARN = "WARN"
HEALTH_FAIL = "FAIL"
HEALTH_UNKNOWN = "UNKNOWN"

_SEVERITY = {HEALTH_FAIL: 3, HEALTH_WARN: 2, HEALTH_UNKNOWN: 1, HEALTH_OK: 0}

# How long since the most recent job activity before we consider the
# pipeline "stale" (i.e. it hasn't produced anything recently).
STALE_AFTER = timedelta(hours=24)

_STATUS_CSS = {
    HEALTH_OK: "SUCCESS",
    HEALTH_WARN: "WARN",
    HEALTH_FAIL: "FAILED",
    HEALTH_UNKNOWN: "NO_DATA",
}

# Display label used by the report-style UI (distinct from the API's
# internal status codes, which stay OK/WARN/FAIL/UNKNOWN for stability).
_REPORT_LABEL = {
    HEALTH_OK: "PASS",
    HEALTH_WARN: "WARNING",
    HEALTH_FAIL: "FAILED",
    HEALTH_UNKNOWN: "PENDING",
}


@dataclass
class HealthCheck:
    key: str
    label: str
    status: str  # HEALTH_OK / HEALTH_WARN / HEALTH_FAIL / HEALTH_UNKNOWN
    message: str
    # Optional fields that make alerts actionable (P1-4).
    # ``stage`` names the affected pipeline stage when the issue is stage-specific.
    stage: str | None = None
    # ``timestamp`` is the most relevant event time, formatted for display.
    timestamp: str | None = None
    # ``next_step`` is a short, plain-language recommended action for the operator.
    next_step: str | None = None

    @property
    def css_status(self) -> str:
        return _STATUS_CSS[self.status]

    @property
    def report_label(self) -> str:
        return _REPORT_LABEL[self.status]


@dataclass
class HealthReport:
    overall: str
    checks: list[HealthCheck]

    @property
    def css_status(self) -> str:
        return _STATUS_CSS[self.overall]

    @property
    def report_label(self) -> str:
        return _REPORT_LABEL[self.overall]


def _check_log_availability(overview: PipelineOverview) -> HealthCheck:
    if overview.log_file_exists:
        return HealthCheck(
            "log_availability",
            "Log Availability",
            HEALTH_OK,
            "logs/application.log is present and readable",
        )
    return HealthCheck(
        "log_availability",
        "Log Availability",
        HEALTH_UNKNOWN,
        "logs/application.log not found — pipeline has not been run in this environment",
        next_step=(
            "Run the pipeline at least once: "
            "`uv run python3 -m elt_pipeline --run-pipeline`. "
            "The log file is created automatically on first execution."
        ),
    )


def _check_last_run_outcome(overview: PipelineOverview) -> HealthCheck:
    if not overview.recent_runs:
        return HealthCheck(
            "last_run",
            "Latest Execution Status",
            HEALTH_UNKNOWN,
            "No pipeline start or completion event has been recorded yet.",
            next_step=(
                "Run the pipeline: `uv run python3 -m elt_pipeline --run-pipeline`. "
                "Once at least one run completes, its status will appear here."
            ),
        )
    latest = overview.recent_runs[0]
    if latest.status == STATUS_SUCCESS:
        return HealthCheck(
            "last_run",
            "Latest Execution Status",
            HEALTH_OK,
            f"Latest run completed successfully.",
            timestamp=latest.timestamp,
        )
    if latest.status == STATUS_FAILED:
        # Find which stage failed, if stage-level evidence is available.
        failed_stages = [
            s.stage.label for s in overview.stages if s.status == STATUS_FAILED
        ]
        stage_hint = (
            f"Affected stage(s): {', '.join(failed_stages)}. " if failed_stages else ""
        )
        return HealthCheck(
            "last_run",
            "Latest Execution Status",
            HEALTH_FAIL,
            f"Latest run failed. {stage_hint}",
            stage=failed_stages[0] if failed_stages else None,
            timestamp=latest.timestamp,
            next_step=(
                "Open Technical Details → Recent Logs to read the full traceback. "
                "Consult docs/runbooks/pipeline_failure.md for stage-specific recovery steps."
            ),
        )
    if latest.status == STATUS_RUNNING:
        started_at = _parse_ts(latest.timestamp)
        stale = started_at is not None and datetime.now() - started_at > STALE_AFTER
        if stale:
            return HealthCheck(
                "last_run",
                "Latest Execution Status",
                HEALTH_WARN,
                "A pipeline start was recorded, but no completion event has been detected "
                "and the start is older than 24 hours. The run is likely stale or was interrupted.",
                timestamp=latest.timestamp,
                next_step=(
                    "Check whether the pipeline process is still running: `ps aux | grep elt_pipeline`. "
                    "If not, inspect logs/application.log for the last log line before the process stopped. "
                    "Then re-run the pipeline from the failing stage."
                ),
            )
        return HealthCheck(
            "last_run",
            "Latest Execution Status",
            HEALTH_WARN,
            "Pipeline started but no completion event detected yet. "
            "The run may still be in progress.",
            timestamp=latest.timestamp,
            next_step=(
                "Wait for the run to finish, then refresh. "
                "If the pipeline appears stuck, check logs/application.log for the last activity."
            ),
        )
    return HealthCheck(
        "last_run",
        "Latest Execution Status",
        HEALTH_UNKNOWN,
        "Unable to determine the latest run outcome from the available log evidence.",
        timestamp=latest.timestamp,
        next_step="Inspect logs/application.log directly for the most recent pipeline events.",
    )


def _check_job_failures(overview: PipelineOverview) -> HealthCheck:
    failed = [
        f"{stage.stage.label} / {job.job.label}"
        for stage in overview.stages
        for job in stage.jobs
        if job.status == STATUS_FAILED
    ]
    if failed:
        # Group by stage for the stage field.
        failed_stages = list(dict.fromkeys(
            stage.stage.label for stage in overview.stages
            for job in stage.jobs if job.status == STATUS_FAILED
        ))
        return HealthCheck(
            "job_failures",
            "Job Failures",
            HEALTH_FAIL,
            f"{len(failed)} job(s) reporting failure: {', '.join(failed)}",
            stage=failed_stages[0] if failed_stages else None,
            next_step=(
                "Open Pipeline Run → the affected stage to read the per-job detail message. "
                "Then consult docs/runbooks/pipeline_failure.md for that stage's recovery steps."
            ),
        )
    known = [
        job for stage in overview.stages for job in stage.jobs
        if job.status in (STATUS_SUCCESS, STATUS_RUNNING)
    ]
    if not known:
        return HealthCheck(
            "job_failures", "Job Failures", HEALTH_UNKNOWN,
            "No job-level completion or failure evidence is available",
            next_step=(
                "Run the pipeline to generate job-level log events: "
                "`uv run python3 -m elt_pipeline --run-pipeline`."
            ),
        )
    return HealthCheck("job_failures", "Job Failures", HEALTH_OK,
                       "No logged job failure found")


def _check_staleness(overview: PipelineOverview) -> HealthCheck:
    timestamps = [
        job.last_activity
        for stage in overview.stages
        for job in stage.jobs
        if job.last_activity is not None
    ]
    if not timestamps:
        return HealthCheck(
            "staleness",
            "Data Freshness",
            HEALTH_UNKNOWN,
            "No job has produced output yet, so freshness cannot be evaluated",
            next_step=(
                "Run the pipeline to generate output: "
                "`uv run python3 -m elt_pipeline --run-pipeline`."
            ),
        )

    latest = max(timestamps)
    age = datetime.now() - latest
    if age > STALE_AFTER:
        hours = int(age.total_seconds() // 3600)
        return HealthCheck(
            "staleness",
            "Data Freshness",
            HEALTH_WARN,
            f"Most recent job output is {hours}h old.",
            timestamp=latest.strftime("%Y-%m-%d %H:%M:%S"),
            next_step=(
                "If the pipeline runs on a schedule, verify it is still running. "
                "Otherwise, re-run the pipeline manually: "
                "`uv run python3 -m elt_pipeline --run-pipeline`."
            ),
        )
    return HealthCheck(
        "staleness",
        "Data Freshness",
        HEALTH_OK,
        f"Most recent output was produced at {latest:%Y-%m-%d %H:%M:%S} (local).",
    )


def _check_pipeline_continuity(overview: PipelineOverview) -> HealthCheck:
    """Report output availability separately from execution state.

    This check is explicitly labelled as STORAGE AVAILABILITY so it is never
    confused with pipeline execution health.
    """
    missing = [layer.label for layer in overview.storage_layers if not layer.has_data]
    if not overview.storage_layers:
        return HealthCheck("continuity", "Storage Availability", HEALTH_UNKNOWN,
                           "Storage availability was not evaluated")
    if missing and len(missing) == len(overview.storage_layers):
        return HealthCheck(
            "continuity", "Storage Availability", HEALTH_UNKNOWN,
            "No layer output detected in any configured storage path. "
            "This reflects storage presence only — not pipeline execution success.",
            next_step=(
                "Run the pipeline at least once: "
                "`uv run python3 -m elt_pipeline --run-pipeline`."
            ),
        )
    if missing:
        return HealthCheck(
            "continuity", "Storage Availability", HEALTH_WARN,
            f"No output detected in: {', '.join(missing)}. "
            "Storage presence only — does not indicate whether processing succeeded.",
            next_step=(
                "Run the missing stage or the full pipeline. "
                "If the stage runs but output is still absent, check the path "
                "configured in dashboard/services/pipeline_registry.py."
            ),
        )
    return HealthCheck(
        "continuity", "Storage Availability", HEALTH_OK,
        "Output is present in all configured local storage paths. "
        "This confirms storage presence only — processing status is reported separately "
        "under Latest Execution Status.",
    )


def _check_dbt_tests(overview: PipelineOverview, summary: DbtRunSummary | None) -> HealthCheck:
    if summary is None or summary.tests_total == 0:
        return HealthCheck(
            "dbt_tests", "Gold dbt Tests", HEALTH_UNKNOWN,
            "No dbt run-results report is available",
            next_step=(
                "Run the Gold dbt build: `uv run python scripts/run_gold_dbt.py`. "
                "The run-results.json file is written after a successful dbt run."
            ),
        )

    generated_at = None
    if summary.generated_at:
        try:
            generated_at = datetime.fromisoformat(summary.generated_at.replace("Z", "+00:00"))
        except ValueError:
            generated_at = None
    latest_start = _parse_ts(overview.last_run_started)
    if generated_at and latest_start:
        local_start = latest_start.astimezone()
        if generated_at <= local_start:
            return HealthCheck(
                "dbt_tests", "Gold dbt Tests", HEALTH_UNKNOWN,
                f"The saved dbt test report predates the latest orchestration start. "
                "Results may be stale.",
                timestamp=summary.generated_at,
                next_step=(
                    "Re-run the Gold dbt build after the pipeline completes: "
                    "`uv run python scripts/run_gold_dbt.py`."
                ),
            )

    failed = summary.tests_failed + summary.tests_errored
    if failed:
        failed_names = ", ".join(test.name for test in summary.failed_tests[:5])
        suffix = f" ({failed_names})" if failed_names else ""
        return HealthCheck(
            "dbt_tests", "Gold dbt Tests", HEALTH_FAIL,
            f"{failed} test(s) failed or errored{suffix}",
            stage="Gold / dbt Transformation",
            timestamp=summary.generated_at,
            next_step=(
                "Open Data Quality → dbt Tests for the full test failure list. "
                "Fix the failing model or source data, then re-run: "
                "`uv run python scripts/run_gold_dbt.py`."
            ),
        )
    if summary.tests_warned or summary.tests_skipped:
        return HealthCheck(
            "dbt_tests", "Gold dbt Tests", HEALTH_WARN,
            f"{summary.tests_warned} warning(s) and {summary.tests_skipped} skipped test(s) "
            "in the last recorded dbt run.",
            stage="Gold / dbt Transformation",
            timestamp=summary.generated_at,
            next_step="Review warnings in Data Quality → dbt Tests. Skipped tests may indicate missing data.",
        )
    return HealthCheck(
        "dbt_tests", "Gold dbt Tests", HEALTH_OK,
        f"{summary.tests_passed} test(s) passed in the last recorded dbt run.",
        timestamp=summary.generated_at,
    )


def build_health_report(overview: PipelineOverview,
                        dbt_summary: DbtRunSummary | None = None) -> HealthReport:
    logger.info("build_health_report started")
    checks = [
        _check_log_availability(overview),
        _check_last_run_outcome(overview),
        _check_job_failures(overview),
        _check_staleness(overview),
        _check_pipeline_continuity(overview),
        _check_dbt_tests(overview, dbt_summary),
    ]

    overall = HEALTH_OK
    for check in checks:
        if _SEVERITY[check.status] > _SEVERITY[overall]:
            overall = check.status

    return HealthReport(overall=overall, checks=checks)
