"""Merge branch heads for linear history."""

from __future__ import annotations

revision = "0003"
down_revision = ("0002a", "0002b")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge branches by creating empty revision."""
    pass


def downgrade() -> None:
    """Downgrade by doing nothing."""
    pass
