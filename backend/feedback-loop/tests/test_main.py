"""Tests for feedback loop main endpoints."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from feedback_loop import ABTestManager  # noqa: E402
import feedback_loop.main as main  # noqa: E402
from feedback_loop.auth import create_access_token  # noqa: E402
from backend.shared.db import Base, SessionLocal, engine, models  # noqa: E402


def test_impression_conversion_allocation(tmp_path) -> None:
    """Recorded events should influence allocation."""
    main.manager = ABTestManager(database_url="sqlite:///:memory:")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        session.add(models.UserRole(username="admin", role="admin"))
        session.commit()
    client = TestClient(main.app)

    resp = client.post("/impression", params={"variant": "A"})
    assert resp.status_code == 200

    resp = client.post("/conversion", params={"variant": "B"})
    assert resp.status_code == 200

    resp = client.get("/allocation", params={"total_budget": 100})
    assert resp.status_code == 403

    token = create_access_token({"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/allocation", params={"total_budget": 100}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {"variant_a", "variant_b"}


def test_stats_endpoint(tmp_path) -> None:
    """/stats should return conversion totals."""
    main.manager = ABTestManager(database_url="sqlite:///:memory:")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        session.add(models.UserRole(username="admin", role="admin"))
        session.commit()
    client = TestClient(main.app)

    for _ in range(3):
        client.post("/conversion", params={"variant": "A"})
    for _ in range(2):
        client.post("/conversion", params={"variant": "B"})

    resp = client.get("/stats")
    assert resp.status_code == 403
    token = create_access_token({"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/stats", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"conversions_a": 3, "conversions_b": 2}
