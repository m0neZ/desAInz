"""
Empty revision.

Revision ID: 5130a8662f39
Revises: 0002
Create Date: 2025-07-18 19:01:07.890668
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5130a8662f39"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply empty upgrade."""
    pass


def downgrade() -> None:
    """Revert empty upgrade."""
    pass
