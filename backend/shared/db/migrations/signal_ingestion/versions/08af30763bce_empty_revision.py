"""
Empty revision.

Revision ID: 08af30763bce
Revises: 0002
Create Date: 2025-07-18 19:01:02.501080
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "08af30763bce"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply empty upgrade."""
    pass


def downgrade() -> None:
    """Revert empty upgrade."""
    pass
