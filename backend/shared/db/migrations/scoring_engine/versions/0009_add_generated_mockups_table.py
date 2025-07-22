"""Add generated_mockups table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create generated_mockups table."""
    op.create_table(
        "generated_mockups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("prompt", sa.String(), nullable=False),
        sa.Column("num_inference_steps", sa.Integer, nullable=False),
        sa.Column("seed", sa.Integer, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    """Drop generated_mockups table."""
    op.drop_table("generated_mockups")
