"""Merge heads after generated_mockups."""

from __future__ import annotations

revision = "0010"
down_revision = ("0009", "0002")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge branches."""
    pass


def downgrade() -> None:
    """Downgrade merge revision."""
    pass
