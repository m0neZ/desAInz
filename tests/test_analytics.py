"""Tests for the analytics API."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from typing import Iterator

import pytest

from backend.analytics import api
from backend.analytics.auth import create_access_token
from backend.shared.db import Base, models

SessionLocal = sessionmaker()


@pytest.fixture(autouse=True)
def _analytics_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Provide isolated database for analytics tests."""
    db_path = tmp_path / "analytics.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)
    globals()["SessionLocal"] = SessionLocal
    monkeypatch.setattr(api, "SessionLocal", SessionLocal, raising=False)
    monkeypatch.setattr(api, "engine", engine, raising=False)
    monkeypatch.setattr("backend.shared.db.SessionLocal", SessionLocal, raising=False)
    monkeypatch.setattr("backend.shared.db.engine", engine, raising=False)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        ab_test = models.ABTest(listing_id=1, variant="A", conversion_rate=0)
        session.add(ab_test)
        session.commit()
        session.refresh(ab_test)
        session.add_all(
            [
                models.ABTestResult(
                    ab_test_id=ab_test.id,
                    conversions=5,
                    impressions=10,
                    timestamp=datetime.now(timezone.utc),
                ),
                models.ABTestResult(
                    ab_test_id=ab_test.id,
                    conversions=3,
                    impressions=8,
                    timestamp=datetime.now(timezone.utc),
                ),
            ]
        )
        session.add(
            models.MarketplaceMetric(
                listing_id=1,
                clicks=20,
                purchases=2,
                revenue=40.0,
                timestamp=datetime.now(timezone.utc),
            )
        )
        session.add(
            models.MarketplacePerformanceMetric(
                listing_id=1,
                views=5,
                favorites=1,
                orders=1,
                revenue=10.0,
                timestamp=datetime.now(timezone.utc),
            )
        )
        session.add(models.UserRole(username="admin", role="admin"))
        session.commit()
    try:
        yield
    finally:
        engine.dispose()


def test_ab_test_results() -> None:
    """Aggregated AB test results are returned."""
    client = TestClient(api.app)
    resp = client.get("/ab_test_results/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["conversions"] == 8
    assert body["impressions"] == 18


def test_marketplace_metrics() -> None:
    """Marketplace metrics endpoint aggregates rows."""
    client = TestClient(api.app)
    resp = client.get("/marketplace_metrics/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["clicks"] == 20
    assert body["purchases"] == 2
    assert body["revenue"] == 40.0


def test_ab_test_results_export_csv() -> None:
    """Exported A/B test results contain all rows in CSV format."""
    client = TestClient(api.app)
    token = create_access_token({"sub": "admin"})
    resp = client.get(
        "/ab_test_results/1/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert lines[0].startswith("timestamp,conversions,impressions")
    assert len(lines) == 3


def test_marketplace_metrics_export_csv() -> None:
    """Exported marketplace metrics contain all rows in CSV format."""
    client = TestClient(api.app)
    token = create_access_token({"sub": "admin"})
    resp = client.get(
        "/marketplace_metrics/1/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert lines[0].startswith("timestamp,clicks,purchases,revenue")
    assert len(lines) == 2


def test_ab_test_results_export_large_dataset() -> None:
    """CSV export streams large datasets correctly."""
    client = TestClient(api.app)
    token = create_access_token({"sub": "admin"})
    with SessionLocal() as session:
        ab_test_id = session.query(models.ABTest.id).first()[0]
        session.add_all(
            [
                models.ABTestResult(
                    ab_test_id=ab_test_id,
                    conversions=i,
                    impressions=i * 2,
                    timestamp=datetime.now(timezone.utc),
                )
                for i in range(100)
            ]
        )
        session.commit()
    resp = client.get(
        f"/ab_test_results/{ab_test_id}/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert lines[0] == "timestamp,conversions,impressions"
    assert len(lines) == 103


def test_marketplace_metrics_export_large_dataset() -> None:
    """Marketplace metrics export streams large datasets correctly."""
    client = TestClient(api.app)
    token = create_access_token({"sub": "admin"})
    with SessionLocal() as session:
        listing_id = session.query(models.MarketplaceMetric.listing_id).first()[0]
        session.add_all(
            [
                models.MarketplaceMetric(
                    listing_id=listing_id,
                    clicks=i,
                    purchases=1,
                    revenue=float(i),
                    timestamp=datetime.now(timezone.utc),
                )
                for i in range(50)
            ]
        )
        session.commit()
    resp = client.get(
        f"/marketplace_metrics/{listing_id}/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert lines[0] == "timestamp,clicks,purchases,revenue"
    assert len(lines) == 52


def test_performance_metrics_export_csv() -> None:
    """Exported performance metrics contain all rows in CSV format."""
    client = TestClient(api.app)
    token = create_access_token({"sub": "admin"})
    resp = client.get(
        "/performance_metrics/1/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert lines[0].startswith("timestamp,views,favorites,orders,revenue")
    assert len(lines) == 2


def test_performance_metrics_export_large_dataset() -> None:
    """Performance metrics export streams large datasets correctly."""
    client = TestClient(api.app)
    token = create_access_token({"sub": "admin"})
    with SessionLocal() as session:
        listing_id = session.query(
            models.MarketplacePerformanceMetric.listing_id
        ).first()[0]
        session.add_all(
            [
                models.MarketplacePerformanceMetric(
                    listing_id=listing_id,
                    views=i,
                    favorites=1,
                    orders=1,
                    revenue=float(i),
                    timestamp=datetime.now(timezone.utc),
                )
                for i in range(30)
            ]
        )
        session.commit()
    resp = client.get(
        f"/performance_metrics/{listing_id}/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert lines[0] == "timestamp,views,favorites,orders,revenue"
    assert len(lines) == 32
