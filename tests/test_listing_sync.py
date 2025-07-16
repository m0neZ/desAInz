"""Tests for listing synchronization script."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

monitoring_src = Path(__file__).resolve().parents[1] / "backend" / "monitoring" / "src"
sys.path.append(str(monitoring_src))
sys.path.append(str(Path(__file__).resolve().parents[1]))

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import pytest  # noqa: E402

from backend.shared.db import Base, SessionLocal, engine, session_scope  # noqa: E402
from backend.shared.db.models import Listing  # noqa: E402
from scripts import listing_sync  # noqa: E402


def setup_module(module: object) -> None:
    """Create tables for tests."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        Base.metadata.create_all(engine)
    with session_scope() as session:
        from datetime import datetime, UTC

        session.add(
            Listing(
                mockup_id=1,
                price=10.0,
                created_at=datetime.now(UTC),
                state="pending",
            )
        )


def teardown_module(module: object) -> None:
    """Drop tables after tests."""
    Base.metadata.drop_all(engine)


def _mock_response(state: str) -> Any:
    class R:
        status_code = 200

        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, str]:
            return {"state": state}

    return R()


@pytest.mark.usefixtures("monkeypatch")
def test_sync_listing_states_updates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Local state should be updated when remote differs."""

    def fake_get(url: str, timeout: int) -> Any:  # noqa: D401
        return _mock_response("active")

    import requests as req

    monkeypatch.setattr(req, "get", fake_get)
    monkeypatch.setattr(listing_sync, "notify_listing_issue", lambda *args: None)
    updated = listing_sync.sync_listing_states()
    assert updated == 1
    with SessionLocal() as session:
        listing = session.query(Listing).first()
        assert listing is not None
        assert listing.state == "active"
