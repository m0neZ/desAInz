"""End-to-end flow tests using Docker Compose services."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Iterator

import psycopg2
import pytest
import requests


COMPOSE_FILES = ["docker-compose.dev.yml", "docker-compose.test.yml"]
DB_DSN = "postgresql://user:password@localhost:5432/app_test"
S3_ENDPOINT = "http://localhost:9000"


@pytest.fixture(scope="module")
def compose_services() -> Iterator[None]:
    """Spin up required services with docker-compose."""
    cmd = [
        "docker-compose",
        *sum([["-f", f] for f in COMPOSE_FILES], []),
        "up",
        "-d",
        "postgres",
        "redis",
        "minio",
        "scoring-engine",
        "signal-ingestion",
        "marketplace-publisher",
        "mockup-generation",
    ]
    subprocess.run(cmd, check=True)
    try:
        subprocess.run(["scripts/wait-for-services.sh"], check=True)
        yield
    finally:
        subprocess.run(
            [
                "docker-compose",
                *sum([["-f", f] for f in COMPOSE_FILES], []),
                "down",
                "-v",
            ],
            check=True,
        )


def _wait(url: str, timeout: int = 60) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code < 500:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"timed out waiting for {url}")


def test_full_pipeline(compose_services: None, tmp_path: Path) -> None:
    """Verify ingest → score → generate → publish flow."""
    os.environ["APPROVAL_SERVICE_URL"] = "http://localhost:8000"
    _wait("http://localhost:8004/ready")
    _wait("http://localhost:5002/ready")
    _wait("http://localhost:8001/ready")

    resp = requests.post("http://localhost:8004/ingest", timeout=10)
    assert resp.status_code == 200

    with psycopg2.connect(DB_DSN) as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM signals")
        count = cur.fetchone()[0]
    assert count > 0

    payload = {
        "timestamp": "2024-01-01T00:00:00Z",
        "engagement_rate": 1.0,
        "embedding": [0.1],
    }
    resp = requests.post("http://localhost:5002/score", json=payload, timeout=10)
    assert resp.status_code == 200
    score = float(resp.json()["score"])

    out_dir = tmp_path / "out"
    resp = requests.post(
        "http://localhost:8000/generate",
        json={"batches": [["cat"]], "output_dir": str(out_dir)},
        timeout=10,
    )
    assert resp.status_code == 200
    task_id = resp.json()["tasks"][0]
    assert task_id

    img = out_dir / "img.png"
    img.write_bytes(b"x")
    pub_resp = requests.post(
        "http://localhost:8001/publish",
        json={
            "marketplace": "redbubble",
            "design_path": str(img),
            "score": score,
            "metadata": {"title": "t"},
        },
        timeout=10,
    )
    assert pub_resp.status_code == 200
    task = pub_resp.json()["task_id"]

    with psycopg2.connect(DB_DSN) as conn, conn.cursor() as cur:
        cur.execute("SELECT status FROM publish_task WHERE id=%s", (task,))
        status = cur.fetchone()[0]
    assert status in {"pending", "in_progress", "success", "failed"}

    import boto3

    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id="admin",
        aws_secret_access_key="password",
    )
    bucket = os.environ.get("S3_BUCKET", "mockups")
    objs = s3.list_objects_v2(Bucket=bucket).get("Contents", [])
    keys = {obj["Key"] for obj in objs}
    assert any(key.endswith(".png") for key in keys)
