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


def identity(value: object) -> object:
    """Return ``value`` unchanged."""

    return value


def return_true(*_args: object, **_kwargs: object) -> bool:
    """Return ``True`` regardless of arguments."""

    return True


def return_none(*_args: object, **_kwargs: object) -> None:
    """Return ``None`` regardless of arguments."""

    return None


def return_one(*_args: object, **_kwargs: object) -> int:
    """Return ``1`` regardless of arguments."""

    return 1


def return_false(*_args: object, **_kwargs: object) -> bool:
    """Return ``False`` regardless of arguments."""

    return False
