"""Reads logs/application.log, written by spark.common.logger using the
format defined in config/logging_config.yaml:

    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

This module only parses that existing format -- it does not write logs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_LINES_READ = 20000


@dataclass(frozen=True)
class LogEvent:
    timestamp: str
    level: str
    logger_name: str
    message: str


def log_file_path(project_root: Path) -> Path:
    return project_root / "logs" / "application.log"


def read_events(project_root: Path) -> list[LogEvent]:
    """Parse the application log into structured events.

    Returns an empty list gracefully if the log file does not exist yet
    (e.g. the pipeline has never been run in this environment).
    """
    path = log_file_path(project_root)
    if not path.is_file():
        return []

    events: list[LogEvent] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()[-MAX_LINES_READ:]
    except OSError:
        return []

    for line in lines:
        parts = line.rstrip("\n").split(" | ", 3)
        if len(parts) != 4:
            # Continuation line (e.g. a traceback) -- attach to the
            # previous event's message so failures remain readable.
            if events:
                events[-1] = LogEvent(
                    events[-1].timestamp,
                    events[-1].level,
                    events[-1].logger_name,
                    events[-1].message + "\n" + line.rstrip("\n"),
                )
            continue
        timestamp, level, logger_name, message = parts
        events.append(LogEvent(timestamp.strip(), level.strip(), logger_name.strip(), message.strip()))

    return events


def latest_event_matching(events: list[LogEvent], needle: str) -> LogEvent | None:
    """Most recent log event whose message contains `needle` (case-insensitive)."""
    needle_lower = needle.lower()
    for event in reversed(events):
        if needle_lower in event.message.lower():
            return event
    return None


def events_since(events: list[LogEvent], after: LogEvent | None) -> list[LogEvent]:
    if after is None:
        return events
    try:
        idx = events.index(after)
    except ValueError:
        return events
    return events[idx + 1:]
