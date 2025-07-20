"""Pytest utilities used across the test suite."""

from __future__ import annotations

from alembic.config import Config
from alembic.script import ScriptDirectory


def assert_single_head(config_path: str) -> None:
    """Assert that ``alembic heads`` returns a single revision for ``config_path``."""
    cfg = Config(config_path)
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1, f"{config_path} has multiple heads: {heads}"
