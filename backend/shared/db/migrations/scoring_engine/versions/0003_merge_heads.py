"""Merge branch heads for linear history."""

from __future__ import annotations

from alembic import op

revision = "0003"
down_revision = ("0002", "0002")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge branches by creating empty revision."""
    pass


def downgrade() -> None:
    """Downgrade by doing nothing."""
    pass
