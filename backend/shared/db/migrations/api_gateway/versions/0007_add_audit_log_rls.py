"""Add row-level security policy for audit_logs table."""

from __future__ import annotations

from alembic import op

revision = "0007"
down_revision = "7165ae776380"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable RLS on audit_logs table."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY audit_logs_is_self ON audit_logs
        USING (username = current_setting('app.current_username')::text)
        WITH CHECK (username = current_setting('app.current_username')::text)
        """
    )


def downgrade() -> None:
    """Disable RLS on audit_logs table."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP POLICY IF EXISTS audit_logs_is_self ON audit_logs")
    op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY")
