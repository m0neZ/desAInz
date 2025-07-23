"""Integration tests for ``idea_job`` with a SQLite Dagster instance."""

from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Iterator

import vcr
import pytest
from dagster import DagsterInstance

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

ROOT = Path(__file__).resolve().parents[2]
import sys

ORCH_PATH = ROOT / "backend" / "orchestrator"
MONITORING_SRC = ROOT / "backend" / "monitoring" / "src"
sys.path.append(str(ORCH_PATH))
sys.path.append(str(MONITORING_SRC))

from orchestrator.jobs import idea_job


@contextmanager
def _mock_server() -> Iterator[tuple[str, list[str]]]:
    """Run a simple HTTP server and record request paths."""
    calls: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: D401 - helper
            calls.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload: dict[str, object]
            if self.path == "/ingest":
                payload = {"signals": ["s1"]}
            elif self.path == "/score":
                payload = {"score": 1}
            elif self.path == "/generate":
                payload = {"items": ["i1"]}
            elif self.path == "/publish":
                payload = {"task_id": 1}
            else:
                payload = {}
            self.wfile.write(json.dumps(payload).encode())

        def do_GET(self) -> None:  # noqa: D401 - helper
            calls.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"approved": true}')

        def log_message(self, *args: object) -> None:  # noqa: D401 - silence
            return

    server = HTTPServer(("localhost", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    url = f"http://localhost:{server.server_port}"
    try:
        yield url, calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@vcr.use_cassette(
    "tests/integration/cassettes/idea_job.yaml",
    record_mode="new_episodes",
)
@pytest.mark.usefixtures("monkeypatch")
def test_idea_job_sqlite(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run ``idea_job`` using a SQLite Dagster instance."""
    with _mock_server() as (url, calls):
        monkeypatch.setenv("SIGNAL_INGESTION_URL", url)
        monkeypatch.setenv("SCORING_ENGINE_URL", url)
        monkeypatch.setenv("MOCKUP_GENERATION_URL", url)
        monkeypatch.setenv("PUBLISHER_URL", url)
        monkeypatch.setenv("APPROVAL_SERVICE_URL", url)
        instance = DagsterInstance.local_temp(str(tmp_path))
        result = idea_job.execute_in_process(instance=instance)
        assert result.success
        assert sorted(calls) == sorted(
            [
                "/ingest",
                "/score",
                "/generate",
                f"/approvals/{result.dagster_run.run_id}",
                "/publish",
            ]
        )
