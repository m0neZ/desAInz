"""Add analytics tables for A/B tests and marketplace metrics."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analytics tables."""
    op.create_table(
        "ab_test_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ab_test_id", sa.Integer, sa.ForeignKey("ab_tests.id")),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("conversions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        op.f("ix_ab_test_results_ab_test_id"),
        "ab_test_results",
        ["ab_test_id"],
        unique=False,
    )
    op.create_table(
        "marketplace_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("listing_id", sa.Integer, sa.ForeignKey("listings.id")),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("purchases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_index(
        op.f("ix_marketplace_metrics_listing_id"),
        "marketplace_metrics",
        ["listing_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop analytics tables."""
    op.drop_index(
        op.f("ix_marketplace_metrics_listing_id"), table_name="marketplace_metrics"
    )
    op.drop_table("marketplace_metrics")
    op.drop_index(op.f("ix_ab_test_results_ab_test_id"), table_name="ab_test_results")
    op.drop_table("ab_test_results")
