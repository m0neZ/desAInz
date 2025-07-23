"""Merge heads after generated_mockups."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge branches by applying missing tables."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "generated_mockups" not in inspector.get_table_names():
        op.create_table(
            "generated_mockups",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("prompt", sa.String(), nullable=False),
            sa.Column("num_inference_steps", sa.Integer, nullable=False),
            sa.Column("seed", sa.Integer, nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )


def downgrade() -> None:
    """Drop tables added in :func:`upgrade`."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "generated_mockups" in inspector.get_table_names():
        op.drop_table("generated_mockups")
