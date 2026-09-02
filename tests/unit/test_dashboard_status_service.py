from dashboard.services.log_reader import LogEvent
from dashboard.services.status_service import (
    STATUS_SUCCESS,
    _build_recent_runs,
)


def test_recent_runs_include_directly_executed_pipeline() -> None:
    events = [
        LogEvent("2026-08-28 17:28:07", "INFO", "__main__", "Starting ELT pipeline..."),
        LogEvent(
            "2026-08-28 17:28:43",
            "INFO",
            "__main__",
            "ELT pipeline completed successfully in 36.68 seconds.",
        ),
    ]

    runs = _build_recent_runs(events)

    assert [run.status for run in runs] == [STATUS_SUCCESS, "RUNNING"]
    assert runs[0].timestamp == "2026-08-28 17:28:43"
