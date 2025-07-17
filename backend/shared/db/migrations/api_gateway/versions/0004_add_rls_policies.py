"""Add row-level security policies for user tables."""

from __future__ import annotations

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable RLS and create policies."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY user_roles_is_self ON user_roles
        USING (username = current_setting('app.current_username')::text)
        """
    )
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY audit_logs_is_self ON audit_logs
        USING (username = current_setting('app.current_username')::text)
        """
    )


def downgrade() -> None:
    """Drop row-level security policies."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP POLICY IF EXISTS user_roles_is_self ON user_roles")
    op.execute("ALTER TABLE user_roles DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS audit_logs_is_self ON audit_logs")
    op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY")
