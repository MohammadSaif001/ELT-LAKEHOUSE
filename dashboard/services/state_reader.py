from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any] | None:
    """Return parsed JSON, or None if the file is missing/empty/invalid."""
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def read_pipeline_state(project_root: Path) -> dict[str, Any] | None:
    return _read_json(project_root / "metadata" / "pipeline_state" / "state.json")


def read_watermark(project_root: Path) -> dict[str, Any] | None:
    return _read_json(project_root / "metadata" / "watermarks" / "watermark.json")


def read_bronze_checkpoint(project_root: Path) -> dict[str, Any] | None:
    return _read_json(project_root / "metadata" / "checkpoints" / "bronze_checkpoint.json")
