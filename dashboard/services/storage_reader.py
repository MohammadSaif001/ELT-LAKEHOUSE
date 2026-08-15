"""Checks existence/mtime/size of files the pipeline actually writes.

Used as a fallback signal for job status when there is no log line or
state entry to go on -- e.g. storage/generated/generated_orders_data.json
existing tells us the "orders" dataset-generation job has produced
output at some point, even without a log file.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ArtifactInfo:
    exists: bool
    modified_at: datetime | None
    size_bytes: int | None
    is_dir: bool


def inspect(project_root: Path, relative_path: str) -> ArtifactInfo:
    path = project_root / relative_path
    if not path.exists():
        return ArtifactInfo(exists=False, modified_at=None, size_bytes=None, is_dir=False)

    try:
        stat = path.stat()
    except OSError:
        return ArtifactInfo(exists=False, modified_at=None, size_bytes=None, is_dir=False)

    if path.is_dir():
        size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        has_content = any(path.iterdir())
        return ArtifactInfo(
            exists=has_content,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            size_bytes=size,
            is_dir=True,
        )

    return ArtifactInfo(
        exists=stat.st_size > 0,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        size_bytes=stat.st_size,
        is_dir=False,
    )
