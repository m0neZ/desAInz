"""Add roles tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create role and user role tables and seed roles."""
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
    )
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.String(), index=True, nullable=False),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id")),
    )
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
    )
    op.bulk_insert(
        roles_table,
        [
            {"id": 1, "name": "admin"},
            {"id": 2, "name": "editor"},
            {"id": 3, "name": "viewer"},
        ],
    )


def downgrade() -> None:
    """Drop role tables."""
    op.drop_table("user_roles")
    op.drop_table("roles")
