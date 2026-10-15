"""Preserve Betfair back/lay side on immutable market quotes.

Revision ID: 020_market_quote_side
Revises: 019_ingestion_jobs
"""
from alembic import op

revision = "020_market_quote_side"
down_revision = "019_ingestion_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE market_quotes
            ADD COLUMN quote_side TEXT NOT NULL DEFAULT 'BACK'
                CHECK (quote_side IN ('BACK', 'LAY'));
        CREATE INDEX market_quotes_entry_side_idx
            ON market_quotes (entry_id, field_revision, quote_side, source_timestamp DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS market_quotes_entry_side_idx;
        ALTER TABLE market_quotes DROP COLUMN IF EXISTS quote_side;
        """
    )
