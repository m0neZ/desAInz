"""Enable RLS on additional API Gateway tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable RLS policies for API Gateway tables."""
    op.add_column(
        "revoked_tokens",
        sa.Column("username", sa.String(length=50), nullable=False, server_default=""),
    )
    op.add_column(
        "ai_models",
        sa.Column("username", sa.String(length=50), nullable=False, server_default=""),
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE revoked_tokens ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY revoked_tokens_is_self ON revoked_tokens
            USING (username = current_setting('app.current_username')::text)
            WITH CHECK (username = current_setting('app.current_username')::text)
            """,
        )
        op.execute("ALTER TABLE ai_models ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY ai_models_is_self ON ai_models
            USING (username = current_setting('app.current_username')::text)
            WITH CHECK (username = current_setting('app.current_username')::text)
            """,
        )
        op.execute("ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY refresh_tokens_is_self ON refresh_tokens
            USING (username = current_setting('app.current_username')::text)
            WITH CHECK (username = current_setting('app.current_username')::text)
            """,
        )
    op.alter_column("revoked_tokens", "username", server_default=None)
    op.alter_column("ai_models", "username", server_default=None)


def downgrade() -> None:
    """Disable RLS policies for API Gateway tables."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS refresh_tokens_is_self ON refresh_tokens")
        op.execute("ALTER TABLE refresh_tokens DISABLE ROW LEVEL SECURITY")
        op.execute("DROP POLICY IF EXISTS ai_models_is_self ON ai_models")
        op.execute("ALTER TABLE ai_models DISABLE ROW LEVEL SECURITY")
        op.execute("DROP POLICY IF EXISTS revoked_tokens_is_self ON revoked_tokens")
        op.execute("ALTER TABLE revoked_tokens DISABLE ROW LEVEL SECURITY")
    op.drop_column("ai_models", "username")
    op.drop_column("revoked_tokens", "username")
