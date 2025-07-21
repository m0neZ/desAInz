"""Create indexes for common queries.

Revision ID: 830537fd941a
Revises: 5130a8662f39
Create Date: 2025-07-21 02:31:22.922915
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "830537fd941a"
down_revision = "5130a8662f39"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create indexes on ``publish_task.status`` and ``listings.state``."""
    op.create_index(
        op.f("ix_publish_task_status"), "publish_task", ["status"], unique=False
    )
    op.create_index(op.f("ix_listings_state"), "listings", ["state"], unique=False)


def downgrade() -> None:
    """Drop indexes created in :func:`upgrade`."""
    op.drop_index(op.f("ix_listings_state"), table_name="listings")
    op.drop_index(op.f("ix_publish_task_status"), table_name="publish_task")
