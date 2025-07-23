"""Merge branch heads for linear history."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = ("0002a", "0002b")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge branch heads by applying missing operations."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = [col["name"] for col in inspector.get_columns("ideas")]
    if "status" not in columns:
        op.add_column(
            "ideas",
            sa.Column(
                "status",
                sa.String(length=50),
                nullable=False,
                server_default="pending",
            ),
        )

    indexes = [idx["name"] for idx in inspector.get_indexes("signals")]
    if "ix_signals_idea_id" not in indexes:
        op.create_index(
            op.f("ix_signals_idea_id"), "signals", ["idea_id"], unique=False
        )
    if "ix_signals_timestamp" not in indexes:
        op.create_index(
            op.f("ix_signals_timestamp"),
            "signals",
            ["timestamp"],
            unique=False,
        )

    indexes = [idx["name"] for idx in inspector.get_indexes("mockups")]
    if "ix_mockups_idea_id" not in indexes:
        op.create_index(
            op.f("ix_mockups_idea_id"), "mockups", ["idea_id"], unique=False
        )

    indexes = [idx["name"] for idx in inspector.get_indexes("listings")]
    if "ix_listings_mockup_id" not in indexes:
        op.create_index(
            op.f("ix_listings_mockup_id"),
            "listings",
            ["mockup_id"],
            unique=False,
        )

    indexes = [idx["name"] for idx in inspector.get_indexes("ab_tests")]
    if "ix_ab_tests_listing_id" not in indexes:
        op.create_index(
            op.f("ix_ab_tests_listing_id"),
            "ab_tests",
            ["listing_id"],
            unique=False,
        )


def downgrade() -> None:
    """Revert operations applied in :func:`upgrade`."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    indexes = [idx["name"] for idx in inspector.get_indexes("ab_tests")]
    if "ix_ab_tests_listing_id" in indexes:
        op.drop_index(op.f("ix_ab_tests_listing_id"), table_name="ab_tests")

    indexes = [idx["name"] for idx in inspector.get_indexes("listings")]
    if "ix_listings_mockup_id" in indexes:
        op.drop_index(op.f("ix_listings_mockup_id"), table_name="listings")

    indexes = [idx["name"] for idx in inspector.get_indexes("mockups")]
    if "ix_mockups_idea_id" in indexes:
        op.drop_index(op.f("ix_mockups_idea_id"), table_name="mockups")

    indexes = [idx["name"] for idx in inspector.get_indexes("signals")]
    if "ix_signals_timestamp" in indexes:
        op.drop_index(op.f("ix_signals_timestamp"), table_name="signals")
    if "ix_signals_idea_id" in indexes:
        op.drop_index(op.f("ix_signals_idea_id"), table_name="signals")

    columns = [col["name"] for col in inspector.get_columns("ideas")]
    if "status" in columns:
        op.drop_column("ideas", "status")
