"""Create roles and user_roles tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create roles and user_roles tables with defaults."""
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
    )
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id"), nullable=False),
    )
    op.bulk_insert(
        sa.table("roles", sa.column("id"), sa.column("name")),
        [
            {"id": 1, "name": "admin"},
            {"id": 2, "name": "editor"},
            {"id": 3, "name": "viewer"},
        ],
    )


def downgrade() -> None:
    """Drop roles and user_roles tables."""
    op.drop_table("user_roles")
    op.drop_table("roles")
