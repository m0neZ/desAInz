"""
Merge heads from all services.

Revision ID: 4ed6b262010c
Revises: 0014, 0008, e07f77a52d6e, 08af30763bce
Create Date: 2025-07-21 15:15:48.712385

This merge revision ensures the migration history remains linear.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4ed6b262010c"
down_revision = ("0014", "0008", "e07f77a52d6e", "08af30763bce")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the no-op merge migration."""
    pass


def downgrade() -> None:
    """Revert the no-op merge migration."""
    pass
