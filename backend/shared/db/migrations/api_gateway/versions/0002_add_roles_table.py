"""Add user_roles table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_roles table."""
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
        sa.Column("role", sa.String(length=20), nullable=False),
    )


def downgrade() -> None:
    """Drop user_roles table."""
    op.drop_table("user_roles")
