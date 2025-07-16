"""Create mockups table."""

from alembic import op
import sqlalchemy as sa

revision = "moc0001"
down_revision = None
branch_labels = ("mockups",)
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    op.create_table(
        "mockups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
    )


def downgrade() -> None:
    """Revert migration."""
    op.drop_table("mockups")
