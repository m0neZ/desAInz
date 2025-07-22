"""Enable RLS for generated_mockups table."""

from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable RLS on generated_mockups."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE generated_mockups ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY generated_mockups_admin_only ON generated_mockups
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
    """Disable RLS on generated_mockups."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(
        "DROP POLICY IF EXISTS generated_mockups_admin_only ON generated_mockups"
    )
    op.execute("ALTER TABLE generated_mockups DISABLE ROW LEVEL SECURITY")
