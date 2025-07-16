"""Add analytics tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analytics tables."""
    op.create_table(
        "ab_test_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ab_test_id", sa.Integer, sa.ForeignKey("ab_tests.id")),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conversions", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "marketplace_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("listing_id", sa.Integer, sa.ForeignKey("listings.id")),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Drop analytics tables."""
    op.drop_table("marketplace_metrics")
    op.drop_table("ab_test_results")

