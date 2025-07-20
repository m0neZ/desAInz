"""Add refresh_tokens table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create refresh_tokens table."""
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token", sa.String(length=36), nullable=False, unique=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop refresh_tokens table."""
    op.drop_table("refresh_tokens")
