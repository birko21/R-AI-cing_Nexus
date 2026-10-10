"""Add runner status needed for scratchings-aware market comparison.

Revision ID: 012_market_runner_status
Revises: 011_market_quote_phase
"""
from alembic import op

revision = "012_market_runner_status"
down_revision = "011_market_quote_phase"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE market_quotes
            ADD COLUMN runner_status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (runner_status IN ('ACTIVE', 'SCRATCHED', 'RESERVE'));
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE market_quotes DROP COLUMN IF EXISTS runner_status;")
