"""Add tables for score and latency metrics."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create score_metrics and publish_latency_metrics tables."""
    op.create_table(
        "score_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("idea_id", sa.Integer, sa.ForeignKey("ideas.id")),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
    )
    op.create_index(
        op.f("ix_score_metrics_idea_id"), "score_metrics", ["idea_id"], unique=False
    )
    op.create_table(
        "publish_latency_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("idea_id", sa.Integer, sa.ForeignKey("ideas.id")),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("latency_seconds", sa.Float(), nullable=False),
    )
    op.create_index(
        op.f("ix_publish_latency_metrics_idea_id"),
        "publish_latency_metrics",
        ["idea_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop performance metric tables."""
    op.drop_index(
        op.f("ix_publish_latency_metrics_idea_id"),
        table_name="publish_latency_metrics",
    )
    op.drop_table("publish_latency_metrics")
    op.drop_index(op.f("ix_score_metrics_idea_id"), table_name="score_metrics")
    op.drop_table("score_metrics")
