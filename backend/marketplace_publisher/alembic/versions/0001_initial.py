"""Initial migration."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables."""
    op.create_table(
        "publish_jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("marketplace", sa.String, nullable=False),
        sa.Column("listing_id", sa.String, nullable=True),
        sa.Column(
            "state",
            sa.Enum("pending", "in_progress", "success", "failed", name="publishstate"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    """Drop tables."""
    op.drop_table("publish_jobs")
    op.execute("DROP TYPE publishstate")
