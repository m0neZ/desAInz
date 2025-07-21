"""Add HNSW index for embeddings similarity search."""

from __future__ import annotations

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create HNSW index for embedding vector similarity."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.create_index(
        "ix_embeddings_embedding",
        "embeddings",
        ["embedding"],
        postgresql_using="hnsw",
    )


def downgrade() -> None:
    """Drop HNSW index for embeddings."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.drop_index("ix_embeddings_embedding", table_name="embeddings")
