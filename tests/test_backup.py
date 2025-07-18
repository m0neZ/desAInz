"""Tests for the PostgreSQL backup script."""

from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import scripts.backup as backup  # noqa: E402


def test_dump_postgres_creates_and_uploads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Database dump should be uploaded and local file removed."""
    commands: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool = True) -> None:
        commands.append(cmd)
        if cmd[0] == "pg_dump":
            # create dump file to mimic pg_dump output
            dump_index = cmd.index("-f") + 1
            Path(cmd[dump_index]).write_text("dump")

    monkeypatch.setattr(backup, "run", fake_run)

    class FakeDT(datetime):
        @classmethod
        def utcnow(cls) -> "FakeDT":
            return cls(2025, 1, 1, 0, 0, 0)

    monkeypatch.setattr(backup, "datetime", FakeDT)

    backup.dump_postgres(tmp_path, "bucket")

    expected_file = tmp_path / "postgres_20250101000000.sql"
    assert ["pg_dump", "app", "-f", str(expected_file)] in commands
    assert [
        "aws",
        "s3",
        "cp",
        str(expected_file),
        f"s3://bucket/postgres/{expected_file.name}",
    ] in commands
    assert not expected_file.exists()
