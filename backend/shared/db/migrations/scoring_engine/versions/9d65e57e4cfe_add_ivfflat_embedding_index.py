"""Add IVFFlat index for embeddings."""

from __future__ import annotations

from alembic import op

revision = "9d65e57e4cfe"
down_revision = "063f6dbe017c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create IVFFlat index for embedding vector similarity."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.create_index(
        "ix_embeddings_vector",
        "embeddings",
        ["embedding"],
        postgresql_using="ivfflat",
    )


def downgrade() -> None:
    """Drop IVFFlat index for embeddings."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.drop_index("ix_embeddings_vector", table_name="embeddings")
