"""Enable RLS for signals table."""

from __future__ import annotations

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable RLS on signals."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE signals ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY signals_admin_only ON signals
        USING (
            EXISTS (
                SELECT 1 FROM user_roles
                WHERE username = current_setting('app.current_username')::text
                AND role = 'admin'
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM user_roles
                WHERE username = current_setting('app.current_username')::text
                AND role = 'admin'
            )
        )
        """
    )


def downgrade() -> None:
    """Disable RLS on signals."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP POLICY IF EXISTS signals_admin_only ON signals")
    op.execute("ALTER TABLE signals DISABLE ROW LEVEL SECURITY")
