"""Add explicit live/closing phase to immutable market quotes.

Revision ID: 011_market_quote_phase
Revises: 010_market_quotes
"""
from alembic import op

revision = "011_market_quote_phase"
down_revision = "010_market_quotes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE market_quotes
            ADD COLUMN price_phase TEXT NOT NULL DEFAULT 'LIVE'
            CHECK (price_phase IN ('LIVE', 'CLOSING'));
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE market_quotes DROP COLUMN IF EXISTS price_phase;")
