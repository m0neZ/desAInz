"""Tests for signal database constraints."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from backend.shared.db import Base, SessionLocal, engine
from backend.shared.db.models import Signal


def setup_module(module: object) -> None:
    """Create tables for tests."""
    Base.metadata.create_all(engine)


def teardown_module(module: object) -> None:
    """Drop tables after tests."""
    Base.metadata.drop_all(engine)


def test_signal_content_hash_unique() -> None:
    """Duplicated content_hash should raise an integrity error."""
    with SessionLocal() as session:
        sig1 = Signal(
            content_hash="dup",
            timestamp=datetime.utcnow(),
            engagement_rate=0.5,
        )
        session.add(sig1)
        session.commit()
        sig2 = Signal(
            content_hash="dup",
            timestamp=datetime.utcnow(),
            engagement_rate=0.7,
        )
        session.add(sig2)
        with pytest.raises(IntegrityError):
            session.commit()
