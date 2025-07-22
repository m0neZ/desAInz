"""Ensure index for marketplace metrics listing_id."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create index for listing_id on marketplace_metrics if missing."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("marketplace_metrics")]
    if "ix_marketplace_metrics_listing_id" not in indexes:
        op.create_index(
            op.f("ix_marketplace_metrics_listing_id"),
            "marketplace_metrics",
            ["listing_id"],
            unique=False,
        )


def downgrade() -> None:
    """Drop the marketplace_metrics listing_id index if present."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("marketplace_metrics")]
    if "ix_marketplace_metrics_listing_id" in indexes:
        op.drop_index(
            op.f("ix_marketplace_metrics_listing_id"),
            table_name="marketplace_metrics",
        )
