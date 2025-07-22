"""Add RLS policy for generated_mockups."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable RLS on generated_mockups."""
    op.add_column(
        "generated_mockups",
        sa.Column("username", sa.String(length=50), nullable=False, server_default=""),
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE generated_mockups ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY generated_mockups_is_self ON generated_mockups
            USING (username = current_setting('app.current_username')::text)
            WITH CHECK (username = current_setting('app.current_username')::text)
            """,
        )
    op.alter_column("generated_mockups", "username", server_default=None)


def downgrade() -> None:
    """Remove RLS from generated_mockups."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "DROP POLICY IF EXISTS generated_mockups_is_self ON generated_mockups"
        )
        op.execute("ALTER TABLE generated_mockups DISABLE ROW LEVEL SECURITY")
    op.drop_column("generated_mockups", "username")
