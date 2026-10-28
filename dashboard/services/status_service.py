from __future__ import annotations

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import re

from dashboard.services import storage_reader
from dashboard.services import log_reader
from dashboard.services.pipeline_registry import (
    PIPELINE_STAGES,
    STORAGE_LAYERS,
    Job,
    Stage,
)
from dashboard.services import state_reader

"""Combines log_reader, state_reader and storage_reader into the status
model the templates render. This is the only module that decides what
"success / running / failed / no data" means -- everything else here is
raw reads of files the project already produces.
"""


STATUS_NO_DATA = "NO_DATA"
STATUS_RUNNING = "RUNNING"
STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"
STATUS_UNKNOWN = "UNKNOWN"

_STAGE_PRIORITY = {
    STATUS_FAILED: 3,
    STATUS_RUNNING: 2,
    STATUS_SUCCESS: 1,
    STATUS_NO_DATA: 0,
    STATUS_UNKNOWN: 0,
}


@dataclass
class JobStatus:
    job: Job
    status: str
    last_activity: datetime | None
    detail: str


@dataclass
class StageStatus:
    stage: Stage
    status: str
    jobs: list[JobStatus] = field(default_factory=list)
    duration: str | None = None
    last_activity: datetime | None = None
    # Human-readable explanation of why this stage has its current status.
    # None when status is SUCCESS (no explanation needed).
    detail: str | None = None


@dataclass
class LayerStatus:
    key: str
    label: str
    has_data: bool
    modified_at: datetime | None
    size_bytes: int | None
    file_count: int | None = None


@dataclass
class RunEvent:
    timestamp: str
    status: str
    message: str
    execution_id: str | None = None


@dataclass
class PipelineOverview:
    overall_status: str
    stages: list[StageStatus]
    storage_layers: list[LayerStatus]
    recent_runs: list[RunEvent]
    log_file_exists: bool
    pipeline_state_raw: dict | None
    watermark_raw: dict | None
    checkpoint_raw: dict | None
    last_run_started: str | None = None
    last_run_finished: str | None = None
    last_run_duration: str | None = None
    last_successful_run: str | None = None
    latest_run_status: str = STATUS_UNKNOWN
    # Plain-language explanation for the latest_run_status when it is not SUCCESS.
    # None when the status is self-explanatory (SUCCESS) or there is no run.
    latest_run_detail: str | None = None


def _job_status(
    project_root: Path, events: list[log_reader.LogEvent], job: Job,
    latest_run_started: datetime | None = None, execution_open: bool = False,
    latest_execution_id: str | None = None,
) -> JobStatus:
    artifact = (
        storage_reader.inspect(project_root, job.artifact_path)
        if job.artifact_path
        else None
    )
    matching_events = events
    if latest_execution_id:
        matching_events = [
            event for event in events
            if _extract_execution_id(event.message) in (None, latest_execution_id)
        ]
    matched = log_reader.latest_event_matching(matching_events, job.log_match)

    if matched:
        matched_at = _parse_ts(matched.timestamp)
        if latest_run_started and matched_at and matched_at < latest_run_started:
            matched = None

    if matched and matched.level == "ERROR":
        return JobStatus(
            job=job,
            status=STATUS_FAILED,
            last_activity=_parse_ts(matched.timestamp),
            detail=matched.message.splitlines()[0],
        )

    if matched and _message_is_completion(matched.message):
        return JobStatus(
            job=job,
            status=STATUS_SUCCESS,
            last_activity=_parse_ts(matched.timestamp),
            detail=matched.message.splitlines()[0],
        )
    if matched:
        matched_at = _parse_ts(matched.timestamp)
        looks_active = (
            execution_open
            and matched_at is not None
            and datetime.now() - matched_at <= timedelta(hours=24)
        )
        return JobStatus(
            job=job,
            status=STATUS_RUNNING if looks_active else STATUS_UNKNOWN,
            last_activity=matched_at,
            detail=(
                f"Output present ({_fmt_size(artifact.size_bytes)}); latest matching "
                f"event has no completion signal"
                if artifact and artifact.exists
                else (
                    "No completion event detected for the latest matching activity"
                    if looks_active
                    else "A prior activity event exists without a completion signal"
                )
            ),
        )
    if artifact and artifact.exists:
        return JobStatus(
            job=job,
            status=STATUS_UNKNOWN,
            last_activity=artifact.modified_at,
            detail=f"Output present ({_fmt_size(artifact.size_bytes)}); processing status unknown",
        )
    return JobStatus(
        job=job, status=STATUS_UNKNOWN, last_activity=None,
        detail="No output or execution event detected",
    )


def _message_is_completion(message: str) -> bool:
    text = message.lower()
    return any(
        marker in text
        for marker in (
            "completed successfully", "generated successfully", "ingestion completed",
            "ingested successfully", "validation passed", "all ingestion functions completed",
        )
    )


def _fmt_size(size_bytes: int | None) -> str:
    if not size_bytes:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return (
                f"{size_bytes:.0f} {unit}"
                if unit == "B"
                else f"{size_bytes:.1f} {unit}"
            )
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _aggregate(job_statuses: list[JobStatus]) -> str:
    statuses = {j.status for j in job_statuses}
    if not statuses or statuses <= {STATUS_NO_DATA, STATUS_UNKNOWN}:
        return STATUS_UNKNOWN
    if STATUS_FAILED in statuses:
        return STATUS_FAILED
    if STATUS_RUNNING in statuses:
        return STATUS_RUNNING
    if statuses == {STATUS_SUCCESS}:
        return STATUS_SUCCESS
    if STATUS_UNKNOWN in statuses or STATUS_NO_DATA in statuses:
        return STATUS_UNKNOWN
    return STATUS_RUNNING


def _stage_execution(stage: Stage, events: list[log_reader.LogEvent],
                     latest_run_started: datetime | None, execution_open: bool,
                     latest_execution_id: str | None = None
                     ) -> tuple[str, str | None, datetime | None, str | None]:
    """Derive a stage result only from its stage logger, never its old files.

    Returns (status, duration, last_activity, detail).
    ``detail`` is None for SUCCESS; it contains a plain-language explanation for
    every other state so templates can surface the reason without hiding it.
    """
    stage_events = [event for event in events if event.logger_name == stage.logger_name]
    if latest_execution_id:
        stage_events = [
            event for event in stage_events
            if _extract_execution_id(event.message) in (None, latest_execution_id)
        ]
    if latest_run_started:
        stage_events = [
            event for event in stage_events
            if (_parse_ts(event.timestamp) or datetime.min) >= latest_run_started
        ]
    if not stage_events:
        return (
            STATUS_UNKNOWN, None, None,
            f"No log events found for stage '{stage.label}' in the latest run window. "
            "The stage may not have been reached or the log may not cover it.",
        )

    last_activity = _parse_ts(stage_events[-1].timestamp)
    failure = next((event for event in reversed(stage_events) if event.level == "ERROR"), None)
    completion = next(
        (event for event in reversed(stage_events)
         if stage.completion_match.lower() in event.message.lower()),
        None,
    )

    # Failure wins over completion if the error came after the completion marker.
    if failure and (not completion or stage_events.index(failure) > stage_events.index(completion)):
        ts = failure.timestamp
        first_line = failure.message.splitlines()[0]
        return (
            STATUS_FAILED, None, _parse_ts(ts),
            f"Stage '{stage.label}' reported an error at {ts}. "
            f"First error line: {first_line}. "
            "Open Technical Details → Recent Logs to view the full traceback.",
        )

    if completion:
        duration_match = re.search(r"duration_s=([0-9]+(?:\.[0-9]+)?)", completion.message)
        duration = f"{float(duration_match.group(1)):.2f}s" if duration_match else None
        return STATUS_SUCCESS, duration, _parse_ts(completion.timestamp), None

    # No completion, no error — execution may still be running or may have been
    # interrupted without logging an error.
    if execution_open and last_activity and datetime.now() - last_activity <= timedelta(hours=24):
        ts_str = stage_events[-1].timestamp
        return (
            STATUS_RUNNING, None, last_activity,
            f"Stage '{stage.label}' started but has not emitted a completion event. "
            f"Last log entry at {ts_str}. "
            "If the process is no longer running, the stage did not complete successfully. "
            "Check Technical Details → Recent Logs for the last known activity.",
        )

    ts_str = stage_events[-1].timestamp if stage_events else None
    stale_qualifier = (
        " The last known activity is older than 24 hours, so this is not an active run."
        if last_activity and datetime.now() - last_activity > timedelta(hours=24)
        else ""
    )
    return (
        STATUS_UNKNOWN, None, last_activity,
        f"Stage '{stage.label}' has log activity (last: {ts_str}) but no completion "
        f"or error event was detected.{stale_qualifier} "
        "The stage outcome cannot be reliably determined from the available evidence.",
    )


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%d %H:%M:%S"):
        try:
            # Parse the timestamp string using the given format
            return datetime.strptime(ts, fmt)  # DTZ007
        except ValueError:
            continue
    return None


def _extract_execution_id(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(
        r"\b(?:run_id|execution_id|execution|run)\s*[:=]\s*([A-Za-z0-9_.:-]+)",
        value,
        re.IGNORECASE,
    )
    return match.group(1) if match else None


def _build_recent_runs(events: list[log_reader.LogEvent]) -> list[RunEvent]:
    runs: list[RunEvent] = []
    for event in events:
        if event.logger_name not in {"elt_pipeline", "__main__"}:
            continue
        msg = event.message.lower()
        execution_id = _extract_execution_id(event.message)
        if "starting elt pipeline" in msg:
            runs.append(RunEvent(event.timestamp, STATUS_RUNNING, "Pipeline started", execution_id))
        elif "elt pipeline completed successfully" in msg:
            runs.append(RunEvent(event.timestamp, STATUS_SUCCESS, event.message, execution_id))
        elif event.logger_name in {"elt_pipeline", "__main__"} and (
            "pipeline failed with a critical error" in msg
        ):
            runs.append(
                RunEvent(event.timestamp, STATUS_FAILED, event.message.splitlines()[0], execution_id)
            )
    runs.reverse()
    return runs[:25]


def _latest_run_timing(
    runs: list[RunEvent],
) -> tuple[str | None, str | None, str | None]:
    """Pair the most recent completion (SUCCESS/FAILED) with the RUNNING
    start event immediately before it, to report started/finished/duration
    for the latest run. Returns (started, finished, duration) as strings,
    or (None, None, None) / partials when there isn't a clean pair.
    """
    latest = runs[0] if runs else None
    if latest is None:
        return (None, None, None)
    if latest.status == STATUS_RUNNING:
        return (latest.timestamp, None, None)
    finish = latest

    # runs is newest-first; find the RUNNING event right after `finish`
    # in that ordering (i.e. chronologically before it).
    idx = runs.index(finish)
    candidates = [r for r in runs[idx + 1 :] if r.status == STATUS_RUNNING]
    if finish.execution_id:
        start = next(
            (r for r in candidates if r.execution_id == finish.execution_id),
            None,
        )
    else:
        # If the completion has no ID, only pair it with an unlabelled start.
        # This avoids attributing a completion to a different identified run.
        start = next((r for r in candidates if r.execution_id is None), None)
    if start is None:
        return (None, finish.timestamp, None)

    start_dt, finish_dt = _parse_ts(start.timestamp), _parse_ts(finish.timestamp)
    duration = None
    if start_dt and finish_dt and finish_dt >= start_dt:
        duration = f"{(finish_dt - start_dt).total_seconds():.2f}s"
    return (start.timestamp, finish.timestamp, duration)


def get_overview(project_root: Path) -> PipelineOverview:
    logger.info("Building pipeline overview: root=%s", project_root)
    events = log_reader.read_events(project_root)
    recent_runs = _build_recent_runs(events)
    started, finished, duration = _latest_run_timing(recent_runs)
    latest_run = recent_runs[0] if recent_runs else None
    latest_run_status = latest_run.status if latest_run else STATUS_UNKNOWN
    last_successful_run = next(
        (run.timestamp for run in recent_runs if run.status == STATUS_SUCCESS), None
    )
    latest_run_started = _parse_ts(started)
    latest_execution_id = latest_run.execution_id if latest_run else None

    # Build a plain-language explanation for the top-level run status when it
    # is not a clean SUCCESS — callers should display this alongside the badge.
    if latest_run_status == STATUS_UNKNOWN:
        if not recent_runs:
            latest_run_detail: str | None = (
                "No pipeline start or completion event has been recorded yet. "
                "Run the pipeline to populate execution history."
            )
        else:
            latest_run_detail = (
                f"The latest run event at {latest_run.timestamp} did not produce "
                "a recognisable completion or failure signal. "
                "Inspect Technical Details → Recent Logs for the last known state."
            )
    elif latest_run_status == STATUS_RUNNING:
        started_at = _parse_ts(latest_run.timestamp) if latest_run else None
        stale = started_at is not None and datetime.now() - started_at > timedelta(hours=24)
        if stale:
            latest_run_detail = (
                f"A pipeline start was recorded at {latest_run.timestamp}, "
                "but no completion event has been detected and the start is older "
                "than 24 hours. The run is likely stale or was interrupted."
            )
        else:
            latest_run_detail = (
                f"Pipeline started at {latest_run.timestamp}. "
                "No completion event detected — the run may still be in progress."
            )
    elif latest_run_status == STATUS_FAILED:
        latest_run_detail = (
            f"The latest run failed (event at {latest_run.timestamp}). "
            "Open Technical Details → Recent Logs to identify the failing stage."
        )
    else:
        latest_run_detail = None  # SUCCESS is self-explanatory.

    stage_statuses: list[StageStatus] = []
    for stage in PIPELINE_STAGES:
        job_statuses = [
            _job_status(
                project_root, events, job, latest_run_started,
                execution_open=latest_run_status == STATUS_RUNNING,
                latest_execution_id=latest_execution_id,
            )
            for job in stage.jobs
        ]
        stage_status, stage_duration, stage_activity, stage_detail = _stage_execution(
            stage, events, latest_run_started,
            execution_open=latest_run_status == STATUS_RUNNING,
            latest_execution_id=latest_execution_id,
        )
        stage_statuses.append(
            StageStatus(stage=stage, status=stage_status, jobs=job_statuses,
                        duration=stage_duration, last_activity=stage_activity,
                        detail=stage_detail)
        )

    storage_layers = []
    for layer in STORAGE_LAYERS:
        info = storage_reader.inspect(project_root, layer["path"])
        storage_layers.append(
            LayerStatus(
                key=layer["key"],
                label=layer["label"],
                has_data=info.exists,
                modified_at=info.modified_at,
                size_bytes=info.size_bytes,
                file_count=info.file_count,
            )
        )

    # Execution health comes from run events. Output files are reported only
    # through storage_layers and never promote an execution to success.
    overall = latest_run_status

    overview = PipelineOverview(
        overall_status=overall,
        stages=stage_statuses,
        storage_layers=storage_layers,
        recent_runs=recent_runs,
        log_file_exists=log_reader.log_file_path(project_root).is_file(),
        pipeline_state_raw=state_reader.read_pipeline_state(project_root),
        watermark_raw=state_reader.read_watermark(project_root),
        checkpoint_raw=state_reader.read_bronze_checkpoint(project_root),
        last_run_started=started,
        last_run_finished=finished,
        last_run_duration=duration,
        last_successful_run=last_successful_run,
        latest_run_status=latest_run_status,
        latest_run_detail=latest_run_detail,
    )
    logger.info(
        "Pipeline overview built: stages=%d jobs=%d status=%s",
        len(overview.stages),
        sum(len(stage.jobs) for stage in overview.stages),
        overview.overall_status,
    )
    return overview


def get_stage(project_root: Path, stage_key: str) -> StageStatus | None:
    logger.info("Building stage status: stage=%s root=%s", stage_key, project_root)
    overview = get_overview(project_root)
    for stage in overview.stages:
        if stage.stage.key == stage_key:
            return stage
    return None
