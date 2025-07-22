"""Enable RLS on signals table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add username column and enable RLS."""
    op.add_column(
        "signals",
        sa.Column("username", sa.String(length=50), nullable=False, server_default=""),
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE signals ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY signals_is_self_ingest ON signals
            USING (username = current_setting('app.current_username')::text)
            WITH CHECK (username = current_setting('app.current_username')::text)
            """,
        )
    op.alter_column("signals", "username", server_default=None)


def downgrade() -> None:
    """Remove RLS from signals table."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS signals_is_self_ingest ON signals")
        op.execute("ALTER TABLE signals DISABLE ROW LEVEL SECURITY")
    op.drop_column("signals", "username")
