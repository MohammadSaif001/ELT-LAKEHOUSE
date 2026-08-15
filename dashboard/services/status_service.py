"""Combines log_reader, state_reader and storage_reader into the status
model the templates render. This is the only module that decides what
"success / running / failed / no data" means -- everything else here is
raw reads of files the project already produces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from dashboard.services import log_reader, state_reader, storage_reader
from dashboard.services.pipeline_registry import (
    DOWNSTREAM_LAYERS,
    PIPELINE_STAGES,
    Job,
    Stage,
)

STATUS_NO_DATA = "NO_DATA"
STATUS_RUNNING = "RUNNING"
STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"

_STAGE_PRIORITY = {STATUS_FAILED: 3, STATUS_RUNNING: 2, STATUS_SUCCESS: 1, STATUS_NO_DATA: 0}


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


@dataclass
class LayerStatus:
    key: str
    label: str
    has_data: bool
    modified_at: datetime | None
    size_bytes: int | None


@dataclass
class RunEvent:
    timestamp: str
    status: str
    message: str


@dataclass
class PipelineOverview:
    overall_status: str
    stages: list[StageStatus]
    downstream_layers: list[LayerStatus]
    recent_runs: list[RunEvent]
    log_file_exists: bool
    pipeline_state_raw: dict | None
    watermark_raw: dict | None
    checkpoint_raw: dict | None


def _job_status(project_root: Path, events: list[log_reader.LogEvent], job: Job) -> JobStatus:
    artifact = storage_reader.inspect(project_root, job.artifact_path) if job.artifact_path else None
    matched = log_reader.latest_event_matching(events, job.log_match)

    if artifact and artifact.exists:
        return JobStatus(
            job=job,
            status=STATUS_SUCCESS,
            last_activity=artifact.modified_at,
            detail=f"Output present ({_fmt_size(artifact.size_bytes)})",
        )
    if matched and matched.level == "ERROR":
        return JobStatus(
            job=job,
            status=STATUS_FAILED,
            last_activity=None,
            detail=matched.message.splitlines()[0],
        )
    if matched:
        return JobStatus(
            job=job,
            status=STATUS_RUNNING,
            last_activity=None,
            detail=matched.message,
        )
    return JobStatus(job=job, status=STATUS_NO_DATA, last_activity=None, detail="No data available")


def _fmt_size(size_bytes: int | None) -> str:
    if not size_bytes:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.0f} {unit}" if unit == "B" else f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _aggregate(job_statuses: list[JobStatus]) -> str:
    statuses = {j.status for j in job_statuses}
    if not statuses or statuses == {STATUS_NO_DATA}:
        return STATUS_NO_DATA
    if STATUS_FAILED in statuses:
        return STATUS_FAILED
    if STATUS_RUNNING in statuses:
        return STATUS_RUNNING
    if statuses == {STATUS_SUCCESS}:
        return STATUS_SUCCESS
    return STATUS_RUNNING  # mixed success/no-data -> treat as in-progress


def _build_recent_runs(events: list[log_reader.LogEvent]) -> list[RunEvent]:
    runs: list[RunEvent] = []
    for event in events:
        if event.logger_name != "elt_pipeline":
            continue
        msg = event.message.lower()
        if "starting elt pipeline" in msg:
            runs.append(RunEvent(event.timestamp, STATUS_RUNNING, "Pipeline started"))
        elif "completed successfully" in msg:
            runs.append(RunEvent(event.timestamp, STATUS_SUCCESS, event.message))
        elif event.level == "ERROR" or "critical error" in msg:
            runs.append(RunEvent(event.timestamp, STATUS_FAILED, event.message.splitlines()[0]))
    runs.reverse()
    return runs[:25]


def get_overview(project_root: Path) -> PipelineOverview:
    events = log_reader.read_events(project_root)

    stage_statuses: list[StageStatus] = []
    for stage in PIPELINE_STAGES:
        job_statuses = [_job_status(project_root, events, job) for job in stage.jobs]
        stage_statuses.append(
            StageStatus(stage=stage, status=_aggregate(job_statuses), jobs=job_statuses)
        )

    overall = STATUS_NO_DATA
    for s in stage_statuses:
        if _STAGE_PRIORITY[s.status] > _STAGE_PRIORITY[overall]:
            overall = s.status

    downstream = []
    for layer in DOWNSTREAM_LAYERS:
        info = storage_reader.inspect(project_root, layer["path"])
        downstream.append(
            LayerStatus(
                key=layer["key"],
                label=layer["label"],
                has_data=info.exists,
                modified_at=info.modified_at,
                size_bytes=info.size_bytes,
            )
        )

    return PipelineOverview(
        overall_status=overall,
        stages=stage_statuses,
        downstream_layers=downstream,
        recent_runs=_build_recent_runs(events),
        log_file_exists=log_reader.log_file_path(project_root).is_file(),
        pipeline_state_raw=state_reader.read_pipeline_state(project_root),
        watermark_raw=state_reader.read_watermark(project_root),
        checkpoint_raw=state_reader.read_bronze_checkpoint(project_root),
    )


def get_stage(project_root: Path, stage_key: str) -> StageStatus | None:
    overview = get_overview(project_root)
    for stage in overview.stages:
        if stage.stage.key == stage_key:
            return stage
    return None
