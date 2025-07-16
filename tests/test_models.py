"""Tests for model metadata compilation."""

from sqlalchemy import create_engine
from backend.shared.db.base import Base
import backend.signals.models  # noqa: F401
import backend.ideas.models  # noqa: F401
import backend.mockups.models  # noqa: F401
import backend.listings.models  # noqa: F401
import backend.scoring.models  # noqa: F401
import backend.abtests.models  # noqa: F401


def test_create_all() -> None:
    """Ensure tables can be created without errors."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
