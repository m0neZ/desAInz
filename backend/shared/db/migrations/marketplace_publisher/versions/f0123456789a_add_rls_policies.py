"""Enable RLS on marketplace publisher tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "f0123456789a"
down_revision = "e07f77a52d6e"
branch_labels = None
depends_on = None

TABLES = ["publish_task", "webhook_event", "oauth_token"]


def upgrade() -> None:
    """Add username columns and enable RLS policies."""
    for table in TABLES:
        op.add_column(
            table,
            sa.Column(
                "username", sa.String(length=50), nullable=False, server_default=""
            ),
        )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            op.execute(
                f"""
                CREATE POLICY {table}_is_self ON {table}
                USING (username = current_setting('app.current_username')::text)
                WITH CHECK (username = current_setting('app.current_username')::text)
                """
            )
    for table in TABLES:
        op.alter_column(table, "username", server_default=None)


def downgrade() -> None:
    """Drop username columns and disable RLS."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"DROP POLICY IF EXISTS {table}_is_self ON {table}")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    for table in TABLES:
        op.drop_column(table, "username")
