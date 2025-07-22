"""Add RLS for token and model tables."""

from __future__ import annotations

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable RLS for refresh_tokens, revoked_tokens and ai_models."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY refresh_tokens_is_self ON refresh_tokens
        USING (username = current_setting('app.current_username')::text)
        WITH CHECK (username = current_setting('app.current_username')::text)
        """
    )
    op.execute("ALTER TABLE revoked_tokens ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY revoked_tokens_admin_only ON revoked_tokens
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
    op.execute("ALTER TABLE ai_models ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY ai_models_admin_only ON ai_models
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
    """Remove RLS from refresh_tokens, revoked_tokens and ai_models."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP POLICY IF EXISTS ai_models_admin_only ON ai_models")
    op.execute("ALTER TABLE ai_models DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS revoked_tokens_admin_only ON revoked_tokens")
    op.execute("ALTER TABLE revoked_tokens DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS refresh_tokens_is_self ON refresh_tokens")
    op.execute("ALTER TABLE refresh_tokens DISABLE ROW LEVEL SECURITY")
