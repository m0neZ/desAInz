"""Create ideas table."""

from alembic import op
import sqlalchemy as sa

revision = "ide0001"
down_revision = None
branch_labels = ("ideas",)
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    op.create_table(
        "ideas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
    )


def downgrade() -> None:
    """Revert migration."""
    op.drop_table("ideas")
