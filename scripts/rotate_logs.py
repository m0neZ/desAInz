"""Rotate log files daily by archiving and pruning old files."""

from __future__ import annotations

import os
import time
from pathlib import Path

LOG_DIR = Path(os.environ.get("LOG_DIR", "logs"))
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "7"))


def main() -> None:
    """Archive current logs and delete archives older than ``RETENTION_DAYS``."""
    archive = LOG_DIR / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d%H%M%S")

    for log_file in LOG_DIR.glob("*.log"):
        dest = archive / f"{log_file.name}.{timestamp}"
        log_file.rename(dest)
        log_file.touch()

    cutoff = time.time() - RETENTION_DAYS * 86400
    for path in archive.iterdir():
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink()


if __name__ == "__main__":  # pragma: no cover
    main()
