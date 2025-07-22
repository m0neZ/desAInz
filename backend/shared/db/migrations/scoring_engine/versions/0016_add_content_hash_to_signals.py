"""Add unique content_hash column to signals."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add content_hash column."""
    op.add_column(
        "signals",
        sa.Column("content_hash", sa.String(length=32), nullable=False),
    )
    op.create_unique_constraint(
        op.f("uq_signals_content_hash"), "signals", ["content_hash"]
    )


def downgrade() -> None:
    """Remove content_hash column."""
    op.drop_constraint(op.f("uq_signals_content_hash"), "signals", type_="unique")
    op.drop_column("signals", "content_hash")
