"""Add state column to listings table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add state column with default value."""
    op.add_column(
        "listings",
        sa.Column(
            "state",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
    )


def downgrade() -> None:
    """Remove state column."""
    op.drop_column("listings", "state")
