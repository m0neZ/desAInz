"""Tests for the analytics API."""

from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
from backend.analytics import api
from backend.analytics.auth import create_access_token
from backend.shared.db import Base, SessionLocal, engine, models


def setup_module(module: object) -> None:
    """Create tables in the temporary database."""
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
                    timestamp=datetime.now(datetime.UTC),
                ),
                models.ABTestResult(
                    ab_test_id=ab_test.id,
                    conversions=3,
                    impressions=8,
                    timestamp=datetime.now(datetime.UTC),
                ),
            ]
        )
        session.add(
            models.MarketplaceMetric(
                listing_id=1,
                clicks=20,
                purchases=2,
                revenue=40.0,
                timestamp=datetime.now(datetime.UTC),
            )
        )
        session.add(models.UserRole(username="admin", role="admin"))
        session.commit()


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
                    timestamp=datetime.now(datetime.UTC),
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
                    timestamp=datetime.now(datetime.UTC),
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
