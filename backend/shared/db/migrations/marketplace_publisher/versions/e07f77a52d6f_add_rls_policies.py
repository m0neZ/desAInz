"""Enable RLS for marketplace publisher tables."""

from __future__ import annotations

from alembic import op

revision = "e07f77a52d6f"
down_revision = "e07f77a52d6e"
branch_labels = None
depends_on = None

TABLES = ["publish_task", "webhook_event", "oauth_token"]


def upgrade() -> None:
    """Enable RLS on publisher tables."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    policy = (
        "EXISTS (SELECT 1 FROM user_roles WHERE "
        "username = current_setting('app.current_username')::text "
        "AND role = 'admin')"
    )
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_admin_only ON {table}
            USING ({policy})
            WITH CHECK ({policy})
            """
        )


def downgrade() -> None:
    """Disable RLS on publisher tables."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table in reversed(TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_admin_only ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
