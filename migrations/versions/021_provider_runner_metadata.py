"""Persist immutable provider runner metadata with provenance.

Revision ID: 021_provider_runner_metadata
Revises: 020_market_quote_side
"""
from alembic import op

revision = "021_provider_runner_metadata"
down_revision = "020_market_quote_side"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE provider_runner_metadata (
            metadata_id TEXT PRIMARY KEY,
            provider_id TEXT NOT NULL,
            race_id TEXT NOT NULL,
            field_revision TEXT NOT NULL,
            entry_id TEXT NOT NULL,
            selection_id TEXT,
            observed_at TIMESTAMPTZ NOT NULL,
            source_receipt_id TEXT NOT NULL REFERENCES source_receipts(source_receipt_id),
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            rights_state TEXT NOT NULL CHECK (rights_state IN ('SYNTHETIC', 'UNASSESSED', 'APPROVED', 'RESTRICTED', 'REJECTED')),
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (length(trim(provider_id)) > 0),
            CHECK (length(trim(race_id)) > 0),
            CHECK (length(trim(field_revision)) > 0),
            CHECK (length(trim(entry_id)) > 0)
        );

        CREATE TRIGGER provider_runner_metadata_append_only BEFORE UPDATE OR DELETE ON provider_runner_metadata
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX provider_runner_metadata_entry_idx
            ON provider_runner_metadata (provider_id, entry_id, observed_at DESC);
        CREATE INDEX provider_runner_metadata_race_idx
            ON provider_runner_metadata (race_id, field_revision, observed_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS provider_runner_metadata_race_idx;
        DROP INDEX IF EXISTS provider_runner_metadata_entry_idx;
        DROP TRIGGER IF EXISTS provider_runner_metadata_append_only ON provider_runner_metadata;
        DROP TABLE IF EXISTS provider_runner_metadata;
        """
    )
