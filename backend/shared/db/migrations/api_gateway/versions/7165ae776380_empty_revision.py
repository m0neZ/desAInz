"""
Empty revision.

Revision ID: 7165ae776380
Revises: 0006
Create Date: 2025-07-18 19:00:56.795804
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7165ae776380"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply empty upgrade."""
    pass


def downgrade() -> None:
    """Revert empty upgrade."""
    pass
