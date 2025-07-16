"""Re-export shared models for backwards compatibility."""

from __future__ import annotations

from backend.shared.db.models import Weights
from backend.shared.db.base import Base

__all__ = ["Weights", "Base"]
