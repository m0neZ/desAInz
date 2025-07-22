"""Ensure index for AB test result ab_test_id."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create index for ab_test_id on ab_test_results if missing."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("ab_test_results")]
    if "ix_ab_test_results_ab_test_id" not in indexes:
        op.create_index(
            op.f("ix_ab_test_results_ab_test_id"),
            "ab_test_results",
            ["ab_test_id"],
            unique=False,
        )


def downgrade() -> None:
    """Drop the ab_test_results ab_test_id index if present."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("ab_test_results")]
    if "ix_ab_test_results_ab_test_id" in indexes:
        op.drop_index(
            op.f("ix_ab_test_results_ab_test_id"),
            table_name="ab_test_results",
        )
