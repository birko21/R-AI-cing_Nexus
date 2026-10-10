"""Add generic bitemporal fact revisions.

Revision ID: 004_bitemporal_revisions
Revises: 003_race_lifecycle_events
"""
from alembic import op

revision = "004_bitemporal_revisions"
down_revision = "003_race_lifecycle_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE bitemporal_fact_revisions (
            fact_revision_id TEXT PRIMARY KEY,
            fact_key TEXT NOT NULL,
            source_event_at TIMESTAMPTZ NOT NULL,
            published_at TIMESTAMPTZ,
            observed_at TIMESTAMPTZ NOT NULL,
            effective_from TIMESTAMPTZ NOT NULL,
            effective_to TIMESTAMPTZ,
            system_valid_from TIMESTAMPTZ NOT NULL,
            system_valid_to TIMESTAMPTZ,
            source_receipt_id TEXT NOT NULL REFERENCES source_receipts(source_receipt_id),
            receipt_proof BOOLEAN NOT NULL,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (effective_to IS NULL OR effective_to > effective_from),
            CHECK (system_valid_to IS NULL OR system_valid_to > system_valid_from),
            CHECK (published_at IS NULL OR published_at >= source_event_at)
        );

        CREATE TRIGGER bitemporal_fact_revisions_append_only BEFORE UPDATE OR DELETE ON bitemporal_fact_revisions
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX bitemporal_fact_lookup_idx ON bitemporal_fact_revisions (fact_key, system_valid_from DESC, effective_from DESC);
        CREATE INDEX bitemporal_observed_idx ON bitemporal_fact_revisions (observed_at, published_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS bitemporal_fact_revisions_append_only ON bitemporal_fact_revisions;
        DROP TABLE IF EXISTS bitemporal_fact_revisions;
        """
    )
