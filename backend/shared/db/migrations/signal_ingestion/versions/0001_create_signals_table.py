"""Create signals table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create signals table."""
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop signals table."""
    op.drop_table("signals")
