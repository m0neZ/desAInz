"""Add score_benchmarks table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create score_benchmarks table."""
    op.create_table(
        "score_benchmarks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("runs", sa.Integer(), nullable=False),
        sa.Column("uncached_seconds", sa.Float(), nullable=False),
        sa.Column("cached_seconds", sa.Float(), nullable=False),
    )
    op.create_index(
        op.f("ix_score_benchmarks_timestamp"),
        "score_benchmarks",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    """Drop score_benchmarks table."""
    op.drop_index(op.f("ix_score_benchmarks_timestamp"), table_name="score_benchmarks")
    op.drop_table("score_benchmarks")
