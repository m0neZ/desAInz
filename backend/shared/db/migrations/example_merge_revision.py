"""Example Alembic merge revision."""

from __future__ import annotations

revision = "0001_example_merge"
down_revision = ("0001a", "0001b")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge branches by creating an empty revision."""
    pass


def downgrade() -> None:
    """Reverse the merge revision."""
    pass
