"""Reads the application log and parses it into structured events."""

from dataclasses import dataclass, field
import re
import shlex
from pathlib import Path

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

_LOG_FIELD_RE = re.compile(
    r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>\"[^\"]*\"|'[^']*'|\S+)"
)

@dataclass(frozen=True)
class LogEvent:
    timestamp: str
    level: str
    logger_name: str
    message: str
    fields: dict[str, str] = field(default_factory=dict)

    @property
    def normalized_level(self) -> str:
        """Map logging levels to the dashboard's display categories."""
        level = self.level.upper()
        if level in {"WARNING", "WARN"}:
            return "WARNING"
        if level in {"ERROR", "CRITICAL"}:
            return "ERROR"
        return "INFO"


def _parse_fields(message: str) -> dict[str, str]:
    """Extract logfmt fields emitted by the shared runtime logger."""
    fields: dict[str, str] = {}
    for match in _LOG_FIELD_RE.finditer(message):
        value = match.group("value")
        if value[:1] in {"'", '"'}:
            try:
                value = shlex.split(value)[0]
            except ValueError:
                value = value[1:-1]
        fields[match.group("key")] = value
    return fields


def log_file_path(project_root: Path) -> Path:
    return project_root / "logs" / "application.log"


def read_events(project_root: Path) -> list[LogEvent]:
    """Parse the application log into structured events.

    Returns an empty list gracefully if the log file does not exist yet
    (e.g. the pipeline has never been run in this environment).
    """
    logger.info("read_events started")
    path = log_file_path(project_root)
    if not path.is_file():
        return []

    events: list[LogEvent] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        logger.exception("Unable to read application log: path=%s", path)
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
                    events[-1].fields,
                )
            continue
        timestamp, level, logger_name, message = parts
        message = message.strip()
        events.append(
            LogEvent(
                timestamp.strip(),
                level.strip(),
                logger_name.strip(),
                message,
                _parse_fields(message),
            )
        )

    logger.info("Parsed application log: path=%s events=%d", path, len(events))
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
