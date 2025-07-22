"""Re-export shared models for backwards compatibility."""

from __future__ import annotations

from backend.shared.db.base import Base
from backend.shared.db.models import Weights

__all__ = ["Weights", "Base"]
