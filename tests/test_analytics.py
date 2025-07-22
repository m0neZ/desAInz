"""Tests for the analytics API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
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
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
    resp = client.get(
        "/marketplace_metrics/1/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert lines[0].startswith("timestamp,clicks,purchases,revenue")
    assert len(lines) == 2


def test_ab_test_results_export_date_range() -> None:
    """Exported A/B test results respect date bounds."""
    client = TestClient(api.app)
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
    with SessionLocal() as session:
        ts = (
            session.query(models.ABTestResult.timestamp)
            .filter(models.ABTestResult.ab_test_id == 1)
            .order_by(models.ABTestResult.timestamp)
            .first()[0]
        )
    resp = client.get(
        f"/ab_test_results/1/export?end={ts.isoformat()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert len(lines) == 2


def test_marketplace_metrics_export_date_range() -> None:
    """Exported marketplace metrics respect date bounds."""
    client = TestClient(api.app)
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
    with SessionLocal() as session:
        ts = (
            session.query(models.MarketplaceMetric.timestamp)
            .filter(models.MarketplaceMetric.listing_id == 1)
            .order_by(models.MarketplaceMetric.timestamp)
            .first()[0]
        )
    resp = client.get(
        f"/marketplace_metrics/1/export?start={(ts + timedelta(seconds=1)).isoformat()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert len(lines) == 1


def test_performance_metrics_export_date_range() -> None:
    """Exported performance metrics respect date bounds."""
    client = TestClient(api.app)
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
    with SessionLocal() as session:
        ts = (
            session.query(models.MarketplacePerformanceMetric.timestamp)
            .filter(models.MarketplacePerformanceMetric.listing_id == 1)
            .order_by(models.MarketplacePerformanceMetric.timestamp)
            .first()[0]
        )
    resp = client.get(
        f"/performance_metrics/1/export?start={(ts + timedelta(seconds=1)).isoformat()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert len(lines) == 1


def test_ab_test_results_export_large_dataset() -> None:
    """CSV export streams large datasets correctly."""
    client = TestClient(api.app)
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
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
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
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
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
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
    token = create_access_token({"sub": "admin", "roles": ["admin"]})
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
