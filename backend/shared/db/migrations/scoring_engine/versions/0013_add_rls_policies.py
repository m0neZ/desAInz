"""Add row-level security policies for ideas and signals."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable RLS on ideas and signals tables."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.add_column(
        "ideas",
        sa.Column("username", sa.String(length=50), nullable=False, server_default=""),
    )
    op.add_column(
        "signals",
        sa.Column("username", sa.String(length=50), nullable=False, server_default=""),
    )
    op.execute("ALTER TABLE ideas ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY ideas_is_self ON ideas
        USING (username = current_setting('app.current_username')::text)
        WITH CHECK (username = current_setting('app.current_username')::text)
        """
    )
    op.execute("ALTER TABLE signals ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY signals_is_self ON signals
        USING (username = current_setting('app.current_username')::text)
        WITH CHECK (username = current_setting('app.current_username')::text)
        """
    )
    op.alter_column("ideas", "username", server_default=None)
    op.alter_column("signals", "username", server_default=None)


def downgrade() -> None:
    """Remove RLS on ideas and signals tables."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP POLICY IF EXISTS signals_is_self ON signals")
    op.execute("ALTER TABLE signals DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS ideas_is_self ON ideas")
    op.execute("ALTER TABLE ideas DISABLE ROW LEVEL SECURITY")
    op.drop_column("signals", "username")
    op.drop_column("ideas", "username")
