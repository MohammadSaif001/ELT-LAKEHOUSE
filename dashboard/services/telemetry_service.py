"""Derives chart-ready telemetry from the same evidence the rest of the
dashboard already reads (logs/application.log, dbt run_results.json and
storage directories). Nothing here launches work or writes to disk.

Run windows
-----------
The log is split into windows. A window opens at a "starting elt pipeline"
event and closes at the next start (or the end of the log). Inside a window:

* the pipeline logger decides the run outcome (success / failed / incomplete),
* each stage logger gives a first-seen time, a completion time and, when the
  completion message carries ``duration_s=...``, an exact duration,
* every event is counted by level.
"""
from __future__ import annotations

import re
import statistics
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from dashboard.services import log_reader
from dashboard.services.dbt_reader import DbtRunSummary
from dashboard.services.pipeline_registry import PIPELINE_STAGES
from dashboard.services.status_service import PipelineOverview, _parse_ts

PIPELINE_LOGGERS = {"elt_pipeline", "__main__"}
MAX_RUNS = 12          # runs shown in trend charts
MAX_BUCKETS = 24       # time buckets in the event-volume chart

_DURATION_RE = re.compile(r"duration_s=([0-9]+(?:\.[0-9]+)?)")


@dataclass
class StageTiming:
    key: str
    label: str
    status: str                      # SUCCESS / FAILED / RUNNING / UNKNOWN
    start: datetime | None = None
    end: datetime | None = None
    duration_s: float | None = None  # exact if logged, else derived from timestamps
    duration_exact: bool = False
    events: int = 0
    warnings: int = 0
    errors: int = 0


@dataclass
class RunWindow:
    index: int
    started: datetime | None
    finished: datetime | None
    status: str                      # SUCCESS / FAILED / INCOMPLETE / RUNNING
    duration_s: float | None
    stages: list[StageTiming] = field(default_factory=list)
    levels: Counter = field(default_factory=Counter)

    @property
    def event_total(self) -> int:
        return sum(self.levels.values())


def _seconds(a: datetime | None, b: datetime | None) -> float | None:
    if a is None or b is None or b < a:
        return None
    return round((b - a).total_seconds(), 2)


def _split_windows(events: list[log_reader.LogEvent]) -> list[list[log_reader.LogEvent]]:
    """Group events into runs. Events logged before the first start are ignored."""
    windows: list[list[log_reader.LogEvent]] = []
    for event in events:
        is_start = (
            event.logger_name in PIPELINE_LOGGERS
            and "starting elt pipeline" in event.message.lower()
        )
        if is_start:
            windows.append([event])
        elif windows:
            windows[-1].append(event)
    return windows


def _build_window(index: int, window: list[log_reader.LogEvent], is_last: bool) -> RunWindow:
    started = _parse_ts(window[0].timestamp)
    finished: datetime | None = None
    status = "RUNNING" if is_last else "INCOMPLETE"

    for event in window:
        if event.logger_name not in PIPELINE_LOGGERS:
            continue
        msg = event.message.lower()
        if "elt pipeline completed successfully" in msg:
            status, finished = "SUCCESS", _parse_ts(event.timestamp)
        elif "pipeline failed with a critical error" in msg:
            status, finished = "FAILED", _parse_ts(event.timestamp)

    run = RunWindow(
        index=index, started=started, finished=finished, status=status,
        duration_s=_seconds(started, finished),
        levels=Counter(e.normalized_level for e in window),
    )

    for stage in PIPELINE_STAGES:
        stage_events = [e for e in window if e.logger_name == stage.logger_name]
        if not stage_events:
            run.stages.append(StageTiming(stage.key, stage.label, "UNKNOWN"))
            continue
        first = _parse_ts(stage_events[0].timestamp)
        failure = next(
            (e for e in reversed(stage_events) if e.normalized_level == "ERROR"),
            None,
        )
        done = next(
            (e for e in reversed(stage_events)
             if stage.completion_match.lower() in e.message.lower()), None,
        )
        timing = StageTiming(
            key=stage.key, label=stage.label, status="UNKNOWN", start=first,
            events=len(stage_events),
            warnings=sum(e.normalized_level == "WARNING" for e in stage_events),
            errors=sum(e.normalized_level == "ERROR" for e in stage_events),
        )
        if failure and (not done or stage_events.index(failure) > stage_events.index(done)):
            timing.status = "FAILED"
            timing.end = _parse_ts(failure.timestamp)
        elif done:
            timing.status = "SUCCESS"
            timing.end = _parse_ts(done.timestamp)
        elif is_last and status == "RUNNING":
            timing.status = "RUNNING"
            timing.end = _parse_ts(stage_events[-1].timestamp)
        else:
            timing.end = _parse_ts(stage_events[-1].timestamp)

        logged = _DURATION_RE.search(done.message) if done else None
        if logged:
            timing.duration_s, timing.duration_exact = round(float(logged.group(1)), 2), True
        else:
            timing.duration_s = _seconds(timing.start, timing.end)
        run.stages.append(timing)
    return run


def build_runs(events: list[log_reader.LogEvent]) -> list[RunWindow]:
    windows = _split_windows(events)
    return [_build_window(i, w, i == len(windows) - 1) for i, w in enumerate(windows)]


def _fmt_dur(seconds: float | None) -> str:
    if seconds is None:
        return "N/A"
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, rest = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {rest:02.0f}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes):02d}m"


def _iso(value: datetime | None) -> str | None:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


def _event_buckets(events: list[log_reader.LogEvent]) -> dict[str, Any]:
    """Event counts per level, bucketed hourly (<= 48h of log) or daily."""
    stamped = [(_parse_ts(e.timestamp), e.normalized_level) for e in events]
    stamped = [(t, lvl) for t, lvl in stamped if t is not None]
    if not stamped:
        return {"unit": "hour", "buckets": []}
    first, last = min(t for t, _ in stamped), max(t for t, _ in stamped)
    unit = "hour" if last - first <= timedelta(hours=48) else "day"
    step = timedelta(hours=1) if unit == "hour" else timedelta(days=1)

    def floor(t: datetime) -> datetime:
        return t.replace(minute=0, second=0, microsecond=0) if unit == "hour" \
            else t.replace(hour=0, minute=0, second=0, microsecond=0)

    counts: OrderedDict[datetime, Counter] = OrderedDict()
    cursor, end = floor(first), floor(last)
    while cursor <= end:
        counts[cursor] = Counter()
        cursor += step
    for t, lvl in stamped:
        counts[floor(t)][lvl] += 1
    items = list(counts.items())[-MAX_BUCKETS:]
    fmt = "%H:%M" if unit == "hour" else "%b %d"
    return {
        "unit": unit,
        "buckets": [
            {"label": b.strftime(fmt), "full": b.strftime("%Y-%m-%d %H:%M"),
             "info": c.get("INFO", 0) + c.get("DEBUG", 0),
             "warning": c.get("WARNING", 0) + c.get("WARN", 0),
             "error": c.get("ERROR", 0) + c.get("CRITICAL", 0)}
            for b, c in items
        ],
    }


def _stage_for_logger(logger_name: str) -> str:
    for stage in PIPELINE_STAGES:
        if stage.logger_name == logger_name:
            return stage.label.title().replace(" / Dbt", " / dbt")
    if logger_name in PIPELINE_LOGGERS:
        return "Orchestrator"
    return logger_name.rsplit(".", 1)[-1] or logger_name


def build_telemetry(
    project_root: Path,
    overview: PipelineOverview,
    dbt_summary: DbtRunSummary | None,
) -> dict[str, Any]:
    events = log_reader.read_events(project_root)
    runs = build_runs(events)
    recent = runs[-MAX_RUNS:]
    latest = runs[-1] if runs else None

    # ---- run outcomes & durations ------------------------------------
    outcome = Counter(r.status for r in runs)
    finished_runs = [r for r in runs if r.status in ("SUCCESS", "FAILED")]
    success_rate = (
        round(100 * outcome["SUCCESS"] / len(finished_runs)) if finished_runs else None
    )
    ok_durations = [r.duration_s for r in runs if r.status == "SUCCESS" and r.duration_s is not None]
    duration_stats = {
        "avg": round(statistics.mean(ok_durations), 2) if ok_durations else None,
        "median": round(statistics.median(ok_durations), 2) if ok_durations else None,
        "min": min(ok_durations) if ok_durations else None,
        "max": max(ok_durations) if ok_durations else None,
    }
    duration_stats_label = {k: _fmt_dur(v) for k, v in duration_stats.items()}

    gaps = {}
    for a, b in zip(runs, runs[1:]):
        if a.started and b.started:
            gaps[b.index] = round((b.started - a.started).total_seconds() / 3600, 2)

    run_series = [
        {
            "gap_h": gaps.get(r.index),
            "label": r.started.strftime("%d %b %H:%M") if r.started else f"run {r.index + 1}",
            "full": _iso(r.started), "status": r.status,
            "duration": r.duration_s, "duration_label": _fmt_dur(r.duration_s),
            "events": r.event_total,
            "errors": r.levels.get("ERROR", 0), "warnings": r.levels.get("WARNING", 0),
        }
        for r in recent
    ]

    # ---- stage timing (trend + latest gantt) --------------------------
    stage_trend = [
        {
            "label": r.started.strftime("%d %b %H:%M") if r.started else f"run {r.index + 1}",
            "status": r.status,
            "stages": {s.key: s.duration_s for s in r.stages},
        }
        for r in recent
    ]
    stage_meta = [{"key": s.key, "label": s.label.title().replace(" / Dbt", " / dbt")}
                  for s in PIPELINE_STAGES]

    stage_stats = []
    for meta in stage_meta:
        vals = [st.duration_s for r in runs for st in r.stages
                if st.key == meta["key"] and st.status == "SUCCESS" and st.duration_s is not None]
        cur = next((st.duration_s for st in (latest.stages if latest else [])
                    if st.key == meta["key"]), None)
        stage_stats.append({
            "key": meta["key"], "label": meta["label"], "n": len(vals), "latest": cur,
            "min": min(vals) if vals else None, "max": max(vals) if vals else None,
            "median": round(statistics.median(vals), 2) if vals else None,
        })

    gantt = None
    if latest and latest.started:
        origin = latest.started
        horizon = latest.finished or max(
            (s.end for s in latest.stages if s.end), default=origin)
        total = max(_seconds(origin, horizon) or 0.0, 0.001)
        gantt = {
            "total_s": total, "total_label": _fmt_dur(total), "status": latest.status,
            "stages": [
                {
                    "key": s.key, "label": stage_meta[i]["label"], "status": s.status,
                    "offset_s": _seconds(origin, s.start) if s.start else None,
                    "duration_s": s.duration_s,
                    "duration_label": _fmt_dur(s.duration_s),
                    "exact": s.duration_exact, "events": s.events,
                    "warnings": s.warnings, "errors": s.errors,
                }
                for i, s in enumerate(latest.stages)
            ],
        }

    # ---- whole-log event statistics -----------------------------------
    levels = Counter(e.normalized_level for e in events)
    by_logger: dict[str, Counter] = {}
    for e in events:
        by_logger.setdefault(_stage_for_logger(e.logger_name), Counter())[e.normalized_level] += 1
    logger_series = sorted(
        (
            {"label": name, "info": c.get("INFO", 0) + c.get("DEBUG", 0),
             "warning": c.get("WARNING", 0), "error": c.get("ERROR", 0) + c.get("CRITICAL", 0)}
            for name, c in by_logger.items()
        ),
        key=lambda row: -(row["info"] + row["warning"] + row["error"]),
    )[:8]

    first_ts = _parse_ts(events[0].timestamp) if events else None
    last_ts = _parse_ts(events[-1].timestamp) if events else None
    since = datetime.now() - timedelta(hours=24)
    last_24h = sum(1 for e in events if (_parse_ts(e.timestamp) or datetime.min) >= since)

    # ---- dbt ----------------------------------------------------------
    dbt = None
    if dbt_summary:
        dbt = {
            "generated_at": dbt_summary.generated_at,
            "tests": {
                "pass": dbt_summary.tests_passed, "fail": dbt_summary.tests_failed,
                "error": dbt_summary.tests_errored, "warn": dbt_summary.tests_warned,
                "skip": dbt_summary.tests_skipped, "total": dbt_summary.tests_total,
            },
            "models": [
                {"name": m.name, "status": m.status, "seconds": m.execution_seconds}
                for m in sorted(dbt_summary.models, key=lambda m: -(m.execution_seconds or 0))
            ],
            "model_seconds_total": round(
                sum(m.execution_seconds or 0 for m in dbt_summary.models), 2),
        }

    # ---- storage ------------------------------------------------------
    storage = [
        {
            "key": layer.key, "label": layer.label.title(), "present": layer.has_data,
            "bytes": layer.size_bytes or 0,
            "mb": round((layer.size_bytes or 0) / 1048576, 2),
            "modified": _iso(layer.modified_at),
            "files": getattr(layer, "file_count", None),
        }
        for layer in overview.storage_layers
    ]

    # ---- jobs ---------------------------------------------------------
    job_counts = Counter(j.status for s in overview.stages for j in s.jobs)

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kpi": {
            "runs_total": len(runs),
            "runs_success": outcome["SUCCESS"],
            "runs_failed": outcome["FAILED"],
            "runs_incomplete": outcome["INCOMPLETE"] + outcome["RUNNING"],
            "success_rate": success_rate,
            "events_total": len(events),
            "events_24h": last_24h,
            "warnings": levels.get("WARNING", 0),
            "errors": levels.get("ERROR", 0) + levels.get("CRITICAL", 0),
            "log_first": _iso(first_ts), "log_last": _iso(last_ts),
            "jobs_total": sum(job_counts.values()),
            "jobs_success": job_counts.get("SUCCESS", 0),
            "jobs_failed": job_counts.get("FAILED", 0),
            "storage_total_mb": round(sum(s["bytes"] for s in storage) / 1048576, 2),
        },
        "duration_stats": duration_stats,
        "duration_stats_label": duration_stats_label,
        "outcomes": {
            "success": outcome["SUCCESS"], "failed": outcome["FAILED"],
            "incomplete": outcome["INCOMPLETE"] + outcome["RUNNING"],
        },
        "runs": run_series,
        "stage_meta": stage_meta,
        "stage_trend": stage_trend,
        "stage_stats": stage_stats,
        "gantt": gantt,
        "levels": {
            "info": levels.get("INFO", 0) + levels.get("DEBUG", 0),
            "warning": levels.get("WARNING", 0),
            "error": levels.get("ERROR", 0) + levels.get("CRITICAL", 0),
        },
        "event_buckets": _event_buckets(events),
        "by_logger": logger_series,
        "dbt": dbt,
        "storage": storage,
        "stages": [
            {"key": s.stage.key, "label": stage_meta[i]["label"], "status": s.status,
             "jobs": [{"label": j.job.label, "status": j.status} for j in s.jobs]}
            for i, s in enumerate(overview.stages)
        ],
    }
