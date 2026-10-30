"""Read the latest local dbt run-results artifact without exposing its env data."""

from __future__ import annotations

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DbtTestResult:
    name: str
    status: str
    failures: int | None


@dataclass(frozen=True)
class DbtModelResult:
    name: str
    status: str
    execution_seconds: float | None
    completed_at: str | None


@dataclass(frozen=True)
class DbtRunSummary:
    generated_at: str | None
    invocation_started_at: str | None
    tests_total: int
    tests_passed: int
    tests_failed: int
    tests_errored: int
    tests_warned: int
    tests_skipped: int
    models: list[DbtModelResult] = field(default_factory=list)
    failed_tests: list[DbtTestResult] = field(default_factory=list)


def read_run_results(project_root: Path) -> DbtRunSummary | None:
    logger.info("read_run_results started")
    path = project_root / "dbt_gold" / "target" / "run_results.json"
    try:
        if not path.is_file() or path.stat().st_size > 10_000_000:
            return None
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    metadata = payload.get("metadata")
    results = payload.get("results")
    if not isinstance(metadata, dict) or not isinstance(results, list):
        return None

    tests: list[dict[str, Any]] = []
    models: list[DbtModelResult] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        unique_id = result.get("unique_id")
        if not isinstance(unique_id, str) or not unique_id.startswith(
            ("test.", "model.")
        ):
            continue
        name_parts = unique_id.split(".")
        name = name_parts[-1]
        if (
            unique_id.startswith("test.")
            and len(name_parts) > 3
            and re.fullmatch(r"[0-9a-fA-F]{10,}", name)
        ):
            name = name_parts[-2]
        status = str(result.get("status") or "unknown").lower()
        if unique_id.startswith("test."):
            tests.append(
                {"name": name, "status": status, "failures": result.get("failures")}
            )
        else:
            execution_time = result.get("execution_time")
            timings = result.get("timing")
            completed_at = None
            if isinstance(timings, list):
                execute_timing = next(
                    (
                        item
                        for item in reversed(timings)
                        if isinstance(item, dict) and item.get("name") == "execute"
                    ),
                    None,
                )
                if execute_timing and isinstance(
                    execute_timing.get("completed_at"), str
                ):
                    completed_at = execute_timing["completed_at"]
            models.append(
                DbtModelResult(
                    name=name,
                    status=status,
                    execution_seconds=(
                        float(execution_time)
                        if isinstance(execution_time, (int, float))
                        else None
                    ),
                    completed_at=completed_at,
                )
            )

    def count(status: str) -> int:
        return sum(test["status"] == status for test in tests)

    failed_tests = [
        DbtTestResult(
            name=test["name"],
            status=test["status"],
            failures=(
                int(test["failures"]) if isinstance(test["failures"], int) else None
            ),
        )
        for test in tests
        if test["status"] in {"fail", "error"}
    ]
    return DbtRunSummary(
        generated_at=metadata.get("generated_at")
        if isinstance(metadata.get("generated_at"), str)
        else None,
        invocation_started_at=(
            metadata.get("invocation_started_at")
            if isinstance(metadata.get("invocation_started_at"), str)
            else None
        ),
        tests_total=len(tests),
        tests_passed=count("pass"),
        tests_failed=count("fail"),
        tests_errored=count("error"),
        tests_warned=count("warn"),
        tests_skipped=count("skipped"),
        models=models,
        failed_tests=failed_tests,
    )
