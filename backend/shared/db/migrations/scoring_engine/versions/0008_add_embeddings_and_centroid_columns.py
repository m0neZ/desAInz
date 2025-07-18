"""Add embeddings table and centroid columns."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""
    if op.get_context().dialect.name != "sqlite":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "weights",
        sa.Column(
            "source", sa.String(length=50), nullable=False, server_default="global"
        ),
    )
    op.add_column("weights", sa.Column("centroid", Vector(768), nullable=True))
    if op.get_context().dialect.name != "sqlite":
        op.create_unique_constraint(
            op.f("uq_weights_source"), "weights", ["source"]
        )
    op.create_table(
        "embeddings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
    )


def downgrade() -> None:
    """Revert the migration."""
    op.drop_table("embeddings")
    if op.get_context().dialect.name != "sqlite":
        op.drop_constraint(op.f("uq_weights_source"), "weights", type_="unique")
    op.drop_column("weights", "centroid")
    op.drop_column("weights", "source")
