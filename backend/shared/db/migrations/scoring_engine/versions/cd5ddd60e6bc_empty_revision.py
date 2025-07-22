"""
Empty revision.

Revision ID: cd5ddd60e6bc
Revises: 0011
Create Date: 2025-07-18 19:01:05.323587
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cd5ddd60e6bc"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply empty upgrade."""
    pass


def downgrade() -> None:
    """Revert empty upgrade."""
    pass
