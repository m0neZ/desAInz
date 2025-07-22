"""Create webhook_event table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create webhook_event table."""
    op.create_table(
        "webhook_event",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "task_id", sa.Integer, sa.ForeignKey("publish_task.id"), nullable=False
        ),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop webhook_event table."""
    op.drop_table("webhook_event")
