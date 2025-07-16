"""Backward-compatible imports for shared DB utilities."""

from __future__ import annotations

from backend.shared.db import engine, session_scope

__all__ = ["engine", "session_scope"]
