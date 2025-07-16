"""Add audit_logs table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit_logs table."""
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column(
            "timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_table("audit_logs")
