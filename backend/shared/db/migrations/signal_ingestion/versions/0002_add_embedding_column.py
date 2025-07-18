"""Add embedding column."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add embedding column to signals table."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("signals", sa.Column("embedding", Vector(768), nullable=True))


def downgrade() -> None:
    """Remove embedding column."""
    op.drop_column("signals", "embedding")
