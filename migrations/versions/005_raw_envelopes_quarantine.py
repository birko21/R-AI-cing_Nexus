"""Add immutable raw envelopes and quarantine records.

Revision ID: 005_raw_envelopes_quarantine
Revises: 004_bitemporal_revisions
"""
from alembic import op

revision = "005_raw_envelopes_quarantine"
down_revision = "004_bitemporal_revisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE raw_envelopes (
            envelope_id TEXT PRIMARY KEY,
            source_identifier TEXT NOT NULL,
            payload JSONB NOT NULL,
            payload_sha256 TEXT NOT NULL CHECK (length(payload_sha256) = 64),
            schema_version TEXT NOT NULL,
            retrieved_at TIMESTAMPTZ NOT NULL,
            first_observed_at TIMESTAMPTZ NOT NULL,
            published_at TIMESTAMPTZ,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            rights_state TEXT NOT NULL CHECK (rights_state IN ('SYNTHETIC', 'UNASSESSED', 'APPROVED', 'RESTRICTED', 'REJECTED')),
            licence_reference TEXT,
            retrieval_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (published_at IS NULL OR published_at >= first_observed_at),
            CHECK (data_mode <> 'LICENSED' OR licence_reference IS NOT NULL)
        );

        CREATE TABLE quarantine_records (
            quarantine_id TEXT PRIMARY KEY,
            envelope_id TEXT NOT NULL,
            reason_code TEXT NOT NULL CHECK (reason_code IN ('CHECKSUM_MISMATCH', 'INVALID_SCHEMA', 'MISSING_SOURCE_ID', 'UNRESOLVED_IDENTITY', 'RIGHTS_UNASSESSED', 'PARSE_ERROR')),
            detail TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TRIGGER raw_envelopes_append_only BEFORE UPDATE OR DELETE ON raw_envelopes
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER quarantine_records_append_only BEFORE UPDATE OR DELETE ON quarantine_records
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX raw_envelopes_source_observed_idx ON raw_envelopes (source_identifier, first_observed_at DESC);
        CREATE INDEX quarantine_records_reason_idx ON quarantine_records (reason_code, created_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS quarantine_records_append_only ON quarantine_records;
        DROP TRIGGER IF EXISTS raw_envelopes_append_only ON raw_envelopes;
        DROP TABLE IF EXISTS quarantine_records;
        DROP TABLE IF EXISTS raw_envelopes;
        """
    )
