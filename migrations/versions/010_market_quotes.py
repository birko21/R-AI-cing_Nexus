"""Add immutable market quotes and mapping quarantine.

Revision ID: 010_market_quotes
Revises: 009_source_health
"""
from alembic import op

revision = "010_market_quotes"
down_revision = "009_source_health"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE market_quotes (
            quote_id TEXT PRIMARY KEY,
            code TEXT NOT NULL CHECK (code IN ('THOROUGHBRED', 'HARNESS', 'GREYHOUND')),
            race_id TEXT NOT NULL,
            field_revision TEXT NOT NULL,
            entry_id TEXT NOT NULL,
            market_source TEXT NOT NULL,
            market_id TEXT NOT NULL,
            selection_id TEXT NOT NULL,
            market_type TEXT NOT NULL CHECK (market_type IN ('WIN', 'PLACE', 'TOP_N', 'HEAD_TO_HEAD')),
            price_type TEXT NOT NULL CHECK (price_type IN ('DECIMAL', 'FRACTIONAL', 'AMERICAN', 'TOTAL_RETURN')),
            price NUMERIC NOT NULL CHECK ((price_type = 'AMERICAN' AND price <> 0) OR (price_type <> 'AMERICAN' AND price > 0)),
            source_timestamp TIMESTAMPTZ NOT NULL,
            retrieved_at TIMESTAMPTZ NOT NULL,
            in_play BOOLEAN NOT NULL,
            size NUMERIC CHECK (size IS NULL OR size > 0),
            liquidity NUMERIC CHECK (liquidity IS NULL OR liquidity > 0),
            entitlement_reference TEXT NOT NULL,
            source_receipt_id TEXT NOT NULL,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            rights_state TEXT NOT NULL CHECK (rights_state IN ('SYNTHETIC', 'UNASSESSED', 'APPROVED', 'RESTRICTED', 'REJECTED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (source_timestamp <= retrieved_at)
        );

        CREATE TABLE market_mapping_quarantine (
            quarantine_id TEXT PRIMARY KEY,
            quote_id TEXT NOT NULL,
            reason_code TEXT NOT NULL CHECK (reason_code IN ('MISSING_EXACT_MAPPING', 'INVALID_MAPPING', 'INVALID_QUOTE')),
            detail TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TRIGGER market_quotes_append_only BEFORE UPDATE OR DELETE ON market_quotes
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER market_mapping_quarantine_append_only BEFORE UPDATE OR DELETE ON market_mapping_quarantine
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX market_quotes_entry_revision_idx ON market_quotes (entry_id, field_revision, source_timestamp DESC);
        CREATE INDEX market_quotes_source_time_idx ON market_quotes (market_source, retrieved_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS market_mapping_quarantine_append_only ON market_mapping_quarantine;
        DROP TRIGGER IF EXISTS market_quotes_append_only ON market_quotes;
        DROP TABLE IF EXISTS market_mapping_quarantine;
        DROP TABLE IF EXISTS market_quotes;
        """
    )
