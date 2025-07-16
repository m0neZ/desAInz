"""Create signals table."""

from alembic import op
import sqlalchemy as sa

revision = "sig0001"
down_revision = None
branch_labels = ("signals",)
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
    )


def downgrade() -> None:
    """Revert migration."""
    op.drop_table("signals")
