"""Add oauth_token table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e07f77a52d6e"
down_revision = "830537fd941a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ``oauth_token`` table."""
    op.create_table(
        "oauth_token",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("marketplace", sa.String(length=50), nullable=False, unique=True),
        sa.Column("access_token", sa.String(), nullable=True),
        sa.Column("refresh_token", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Drop ``oauth_token`` table."""
    op.drop_table("oauth_token")
