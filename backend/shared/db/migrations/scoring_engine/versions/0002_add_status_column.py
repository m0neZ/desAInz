"""Add status column to ideas table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add status column with default value."""
    op.add_column(
        "ideas",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
    )


def downgrade() -> None:
    """Remove status column."""
    op.drop_column("ideas", "status")
