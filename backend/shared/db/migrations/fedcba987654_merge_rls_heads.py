"""Merge heads after adding RLS policies."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "fedcba987654"
down_revision = ("0017", "0009", "e07f77a52d6f", "0004", "0002", "abcdef123456")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the merge revision."""
    pass


def downgrade() -> None:
    """Downgrade merge revision."""
    pass
