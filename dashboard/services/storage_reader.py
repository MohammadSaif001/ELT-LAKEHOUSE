from __future__ import annotations

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ArtifactInfo:
    exists: bool
    modified_at: datetime | None
    size_bytes: int | None
    is_dir: bool
    file_count: int | None = None


def inspect(project_root: Path, relative_path: str) -> ArtifactInfo:
    logger.info("inspect started")
    path = project_root / relative_path
    if not path.exists():
        return ArtifactInfo(
            exists=False, modified_at=None, size_bytes=None, is_dir=False
        )

    try:
        stat = path.stat()
    except OSError:
        return ArtifactInfo(
            exists=False, modified_at=None, size_bytes=None, is_dir=False
        )

    if path.is_dir():
        files = [f for f in path.rglob("*") if f.is_file()]
        size = sum(f.stat().st_size for f in files)
        # A directory holding only zero-byte placeholder files (e.g. an
        # __init__.py stub) hasn't actually received pipeline output.
        content_files = [f for f in files if f.stat().st_size > 0]
        has_content = bool(content_files)
        modified = max((f.stat().st_mtime for f in content_files), default=None)
        return ArtifactInfo(
            exists=has_content,
            modified_at=datetime.fromtimestamp(modified) if modified else None,
            size_bytes=size,
            is_dir=True,
            file_count=len(content_files),
        )

    return ArtifactInfo(
        exists=stat.st_size > 0,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        size_bytes=stat.st_size,
        is_dir=False,
        file_count=1,
    )
