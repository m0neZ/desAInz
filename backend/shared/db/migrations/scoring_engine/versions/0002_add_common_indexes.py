"""Add indexes for frequent lookups."""

from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create indexes to optimize common queries."""
    op.create_index(op.f("ix_signals_idea_id"), "signals", ["idea_id"], unique=False)
    op.create_index(
        op.f("ix_signals_timestamp"), "signals", ["timestamp"], unique=False
    )
    op.create_index(op.f("ix_mockups_idea_id"), "mockups", ["idea_id"], unique=False)
    op.create_index(
        op.f("ix_listings_mockup_id"), "listings", ["mockup_id"], unique=False
    )
    op.create_index(
        op.f("ix_ab_tests_listing_id"), "ab_tests", ["listing_id"], unique=False
    )


def downgrade() -> None:
    """Drop added indexes."""
    op.drop_index(op.f("ix_ab_tests_listing_id"), table_name="ab_tests")
    op.drop_index(op.f("ix_listings_mockup_id"), table_name="listings")
    op.drop_index(op.f("ix_mockups_idea_id"), table_name="mockups")
    op.drop_index(op.f("ix_signals_timestamp"), table_name="signals")
    op.drop_index(op.f("ix_signals_idea_id"), table_name="signals")
