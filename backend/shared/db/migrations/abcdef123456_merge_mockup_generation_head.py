"""Merge mockup_generation head with previous heads."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "abcdef123456"
down_revision = ("4ed6b262010c", "0001")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the no-op merge migration."""
    pass


def downgrade() -> None:
    """Revert the no-op merge migration."""
    pass
