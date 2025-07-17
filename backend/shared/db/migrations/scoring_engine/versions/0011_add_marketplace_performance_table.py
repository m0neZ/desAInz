"""Add marketplace performance metrics table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create marketplace_performance_metrics table."""
    op.create_table(
        "marketplace_performance_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("listing_id", sa.Integer, sa.ForeignKey("listings.id")),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("favorites", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_index(
        op.f("ix_marketplace_performance_metrics_listing_id"),
        "marketplace_performance_metrics",
        ["listing_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop marketplace_performance_metrics table."""
    op.drop_index(
        op.f("ix_marketplace_performance_metrics_listing_id"),
        table_name="marketplace_performance_metrics",
    )
    op.drop_table("marketplace_performance_metrics")
