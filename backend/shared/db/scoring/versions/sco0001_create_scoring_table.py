"""Create scoring table."""

from alembic import op
import sqlalchemy as sa

revision = "sco0001"
down_revision = None
branch_labels = ("scoring",)
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    op.create_table(
        "scoring",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
    )


def downgrade() -> None:
    """Revert migration."""
    op.drop_table("scoring")
