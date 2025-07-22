"""Add RLS policies for remaining tables."""

from __future__ import annotations

from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

TABLES = [
    "mockups",
    "listings",
    "weights",
    "ab_tests",
    "ab_test_results",
    "marketplace_metrics",
    "marketplace_performance_metrics",
    "ai_models",
    "score_metrics",
    "publish_latency_metrics",
    "embeddings",
    "generated_mockups",
    "score_benchmarks",
]


def upgrade() -> None:
    """Enable RLS on all remaining tables requiring protection."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    policy = (
        "EXISTS (SELECT 1 FROM user_roles WHERE "
        "username = current_setting('app.current_username')::text "
        "AND role = 'admin')"
    )
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_admin_only ON {table}
            USING ({policy})
            WITH CHECK ({policy})
            """
        )


def downgrade() -> None:
    """Disable RLS on all remaining tables."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table in reversed(TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_admin_only ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
