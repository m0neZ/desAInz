"""
Add marketplace perf listing id index.

Revision ID: 7544cf9b2fd7
Revises: 0019
Create Date: 2025-07-22 16:30:59.175652
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7544cf9b2fd7"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create index for listing_id on marketplace_performance_metrics."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [
        idx["name"] for idx in inspector.get_indexes("marketplace_performance_metrics")
    ]
    if "ix_marketplace_perf_listing_id" not in indexes:
        op.create_index(
            "ix_marketplace_perf_listing_id",
            "marketplace_performance_metrics",
            ["listing_id"],
            unique=False,
        )


def downgrade() -> None:
    """Drop the marketplace_performance_metrics listing_id index if present."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [
        idx["name"] for idx in inspector.get_indexes("marketplace_performance_metrics")
    ]
    if "ix_marketplace_perf_listing_id" in indexes:
        op.drop_index(
            "ix_marketplace_perf_listing_id",
            table_name="marketplace_performance_metrics",
        )
