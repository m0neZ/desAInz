"""Initial placeholder migration for API gateway."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables placeholder."""
    pass


def downgrade() -> None:
    """Drop placeholder tables."""
    pass
