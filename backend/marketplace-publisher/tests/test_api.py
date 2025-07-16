"""Tests for the marketplace publisher API."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_publish_and_progress(monkeypatch, tmp_path) -> None:
    """Publish design and check initial progress."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app
    from marketplace_publisher import publisher

    class DummyClient:
        def publish_design(self, design_path, metadata):
            return "1"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()
    publisher._fallback.publish = lambda *args, **kwargs: None  # type: ignore

    with TestClient(app) as client:
        design = tmp_path / "a.png"
        design.write_text("img")
        response = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {"title": "t"},
            },
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        response = client.get(f"/progress/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] in {
            "pending",
            "in_progress",
            "success",
            "failed",
        }


def test_update_and_retry(monkeypatch, tmp_path) -> None:
    """Edit task metadata and trigger retry."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from marketplace_publisher.db import Marketplace
    from marketplace_publisher.main import app
    from marketplace_publisher import publisher

    class DummyClient:
        def publish_design(self, design_path, metadata):
            return "1"

    publisher.CLIENTS[Marketplace.redbubble] = DummyClient()
    publisher._fallback.publish = lambda *args, **kwargs: None  # type: ignore

    with TestClient(app) as client:
        design = tmp_path / "b.png"
        design.write_text("img")
        resp = client.post(
            "/publish",
            json={
                "marketplace": Marketplace.redbubble.value,
                "design_path": str(design),
                "metadata": {"title": "t"},
            },
        )
        task_id = resp.json()["task_id"]

        resp = client.put(f"/tasks/{task_id}", json={"metadata": {"title": "x"}})
        assert resp.status_code == 200

        resp = client.get("/tasks")
        assert resp.status_code == 200
        tasks = {t["id"]: t for t in resp.json()}
        assert tasks[task_id]["metadata"]["title"] == "x"

        resp = client.post(f"/tasks/{task_id}/retry")
        assert resp.status_code == 200
