"""Tests for feedback loop main endpoints."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from feedback_loop import ABTestManager  # noqa: E402
import feedback_loop.main as main  # noqa: E402
from feedback_loop.auth import create_access_token  # noqa: E402
from backend.shared.db import Base, SessionLocal, engine, models  # noqa: E402


def test_impression_conversion_allocation(tmp_path, monkeypatch) -> None:
    """Recorded events should influence allocation."""
    import backend.shared.db as shared_db
    import feedback_loop.ab_testing as abt

    monkeypatch.setattr(shared_db, "register_pool_metrics", lambda *_: None)
    monkeypatch.setattr(abt, "register_pool_metrics", lambda *_: None)
    main.manager = ABTestManager(database_url="sqlite:///:memory:")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        session.add_all(
            [
                models.UserRole(username="admin", role="admin"),
                models.UserRole(username="tester", role="editor"),
            ]
        )
        session.commit()
    client = TestClient(main.app)

    resp = client.post("/impression", params={"variant": "A"})
    assert resp.status_code == 403
    token_editor = create_access_token({"sub": "tester", "roles": ["editor"]})
    headers_editor = {"Authorization": f"Bearer {token_editor}"}
    resp = client.post("/impression", params={"variant": "A"}, headers=headers_editor)
    assert resp.status_code == 200

    resp = client.post("/conversion", params={"variant": "B"})
    assert resp.status_code == 403
    resp = client.post("/conversion", params={"variant": "B"}, headers=headers_editor)
    assert resp.status_code == 200

    resp = client.get("/allocation", params={"total_budget": 100})
    assert resp.status_code == 403

    token = create_access_token({"sub": "admin", "roles": ["admin"]})
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/allocation", params={"total_budget": 100}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {"variant_a", "variant_b"}


def test_stats_endpoint(tmp_path, monkeypatch) -> None:
    """/stats should return conversion totals."""
    import backend.shared.db as shared_db
    import feedback_loop.ab_testing as abt

    monkeypatch.setattr(shared_db, "register_pool_metrics", lambda *_: None)
    monkeypatch.setattr(abt, "register_pool_metrics", lambda *_: None)
    main.manager = ABTestManager(database_url="sqlite:///:memory:")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        session.add_all(
            [
                models.UserRole(username="admin", role="admin"),
                models.UserRole(username="editor", role="editor"),
            ]
        )
        session.commit()
    client = TestClient(main.app)

    token_editor = create_access_token({"sub": "editor", "roles": ["editor"]})
    headers_editor = {"Authorization": f"Bearer {token_editor}"}
    for _ in range(3):
        client.post("/conversion", params={"variant": "A"}, headers=headers_editor)
    for _ in range(2):
        client.post("/conversion", params={"variant": "B"}, headers=headers_editor)

    resp = client.get("/stats")
    assert resp.status_code == 403
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/stats", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"conversions_a": 3, "conversions_b": 2}
