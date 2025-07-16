"""Create core tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables."""
    op.create_table(
        "ideas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("idea_id", sa.Integer, sa.ForeignKey("ideas.id")),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("engagement_rate", sa.Float(), nullable=False),
        sa.Column("details", sa.String(), nullable=True),
    )
    op.create_table(
        "mockups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("idea_id", sa.Integer, sa.ForeignKey("ideas.id")),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("mockup_id", sa.Integer, sa.ForeignKey("mockups.id")),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "weights",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("freshness", sa.Float(), nullable=False, server_default="1"),
        sa.Column("engagement", sa.Float(), nullable=False, server_default="1"),
        sa.Column("novelty", sa.Float(), nullable=False, server_default="1"),
        sa.Column("community_fit", sa.Float(), nullable=False, server_default="1"),
        sa.Column("seasonality", sa.Float(), nullable=False, server_default="1"),
    )
    op.create_table(
        "ab_tests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("listing_id", sa.Integer, sa.ForeignKey("listings.id")),
        sa.Column("variant", sa.String(length=50), nullable=False),
        sa.Column("conversion_rate", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Drop tables."""
    op.drop_table("ab_tests")
    op.drop_table("weights")
    op.drop_table("listings")
    op.drop_table("mockups")
    op.drop_table("signals")
    op.drop_table("ideas")
