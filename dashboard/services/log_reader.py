"""Reads the application log and parses it into structured events."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

# Unquoted values stop at whitespace or a comma ("records=8000, path=..."),
# and quoted values may contain escaped quotes.
_LOG_FIELD_RE = re.compile(
    r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)="
    r"(?P<value>\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|[^\s,]+)"
)

# A real log record starts with a timestamp; anything else is a continuation
# line (traceback, table output) even if it contains " | ".
_EVENT_START_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d+)? \| ")

# Dashboard loggers must not feed the dashboard's own view of the pipeline.
_IGNORED_LOGGER_PREFIXES = ("dashboard.",)

_CACHE: dict[Path, tuple[float, int, list["LogEvent"]]] = {}


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
            quote = value[0]
            value = value[1:-1].replace("\\" + quote, quote)
        fields[match.group("key")] = value
    return fields


def log_file_path(project_root: Path) -> Path:
    return project_root / "logs" / "application.log"


def read_events(project_root: Path) -> list[LogEvent]:
    """Parse the application log into structured events.

    Returns an empty list gracefully if the log file does not exist yet
    (e.g. the pipeline has never been run in this environment). The parsed
    result is cached until the file's modification time or size changes.
    """
    path = log_file_path(project_root)
    try:
        stat = path.stat()
    except OSError:
        return []

    cached = _CACHE.get(path)
    if cached and cached[0] == stat.st_mtime and cached[1] == stat.st_size:
        return cached[2]

    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        logger.exception("Unable to read application log: path=%s", path)
        return []

    events: list[LogEvent] = []
    skipping = False  # True while inside a record from an ignored logger
    for line in lines:
        line = line.rstrip("\n")
        parts = line.split(" | ", 3)
        if len(parts) == 4 and _EVENT_START_RE.match(line):
            timestamp, level, logger_name, message = parts
            logger_name = logger_name.strip()
            skipping = logger_name.startswith(_IGNORED_LOGGER_PREFIXES)
            if skipping:
                continue
            message = message.strip()
            events.append(
                LogEvent(
                    timestamp.strip(),
                    level.strip(),
                    logger_name,
                    message,
                    _parse_fields(message),
                )
            )
        elif events and not skipping:
            # Continuation line (e.g. a traceback or table output): attach it
            # to the previous event so failures remain readable.
            prev = events[-1]
            events[-1] = LogEvent(
                prev.timestamp,
                prev.level,
                prev.logger_name,
                prev.message + "\n" + line,
                prev.fields,
            )

    _CACHE[path] = (stat.st_mtime, stat.st_size, events)
    logger.debug("Parsed application log: path=%s events=%d", path, len(events))
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
    return events[idx + 1 :]
