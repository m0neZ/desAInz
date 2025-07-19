"""Add columns storing mockup metadata."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "cd5ddd60e6bc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add columns for mockup storage URI and metadata."""
    op.add_column(
        "generated_mockups",
        sa.Column("image_uri", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "generated_mockups",
        sa.Column("title", sa.String(length=200), nullable=False, server_default=""),
    )
    op.add_column(
        "generated_mockups",
        sa.Column("description", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "generated_mockups",
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    """Remove mockup storage and metadata columns."""
    op.drop_column("generated_mockups", "tags")
    op.drop_column("generated_mockups", "description")
    op.drop_column("generated_mockups", "title")
    op.drop_column("generated_mockups", "image_uri")
