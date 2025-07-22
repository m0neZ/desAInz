"""Create publish_task table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create publish_task table."""
    op.create_table(
        "publish_task",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("marketplace", sa.String(length=50), nullable=False),
        sa.Column("design_path", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.String(), nullable=True),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="pending"
        ),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop publish_task table."""
    op.drop_table("publish_task")
