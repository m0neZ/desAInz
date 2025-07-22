"""Add composite index for score_metrics.

Revision ID: 063f6dbe017c
Revises: 7544cf9b2fd7
Create Date: 2025-08-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "063f6dbe017c"
down_revision = "7544cf9b2fd7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create index for (idea_id, timestamp) on score_metrics if missing."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("score_metrics")]
    if "ix_score_metrics_idea_id_timestamp" not in indexes:
        op.create_index(
            "ix_score_metrics_idea_id_timestamp",
            "score_metrics",
            ["idea_id", "timestamp"],
            unique=False,
        )


def downgrade() -> None:
    """Drop the score_metrics idea_id_timestamp index if present."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("score_metrics")]
    if "ix_score_metrics_idea_id_timestamp" in indexes:
        op.drop_index(
            "ix_score_metrics_idea_id_timestamp",
            table_name="score_metrics",
        )
