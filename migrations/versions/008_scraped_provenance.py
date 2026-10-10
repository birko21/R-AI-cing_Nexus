"""Add immutable scraped-source receipts and replay fixtures.

Revision ID: 008_scraped_provenance
Revises: 007_model_registry
"""
from alembic import op

revision = "008_scraped_provenance"
down_revision = "007_model_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE scraped_replay_fixtures (
            fixture_id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            content_sha256 TEXT NOT NULL CHECK (length(content_sha256) = 64),
            parser_version TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE scraped_source_receipts (
            receipt_id TEXT PRIMARY KEY,
            envelope_id TEXT NOT NULL REFERENCES raw_envelopes(envelope_id),
            retrieval_url TEXT NOT NULL,
            retrieved_at TIMESTAMPTZ NOT NULL,
            content_sha256 TEXT NOT NULL CHECK (length(content_sha256) = 64),
            parser_version TEXT NOT NULL,
            data_mode TEXT NOT NULL CHECK (data_mode = 'SCRAPED_PUBLIC'),
            rights_state TEXT NOT NULL CHECK (rights_state IN ('UNASSESSED', 'APPROVED', 'RESTRICTED', 'REJECTED')),
            retention_until TIMESTAMPTZ,
            replay_fixture_id TEXT NOT NULL REFERENCES scraped_replay_fixtures(fixture_id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TRIGGER scraped_replay_fixtures_append_only BEFORE UPDATE OR DELETE ON scraped_replay_fixtures
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER scraped_source_receipts_append_only BEFORE UPDATE OR DELETE ON scraped_source_receipts
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX scraped_source_receipts_retention_idx ON scraped_source_receipts (retention_until, retrieved_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS scraped_source_receipts_append_only ON scraped_source_receipts;
        DROP TRIGGER IF EXISTS scraped_replay_fixtures_append_only ON scraped_replay_fixtures;
        DROP TABLE IF EXISTS scraped_source_receipts;
        DROP TABLE IF EXISTS scraped_replay_fixtures;
        """
    )
