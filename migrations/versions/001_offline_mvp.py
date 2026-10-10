"""Create the append-only offline MVP schema.

Revision ID: 001_offline_mvp
Revises:
"""
from alembic import op

revision = "001_offline_mvp"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE schema_migration_checksums (
            revision TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE source_receipts (
            source_receipt_id TEXT PRIMARY KEY,
            source_identifier TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL CHECK (length(payload_sha256) = 64),
            schema_version TEXT NOT NULL,
            first_observed_at TIMESTAMPTZ NOT NULL,
            published_at TIMESTAMPTZ,
            rights_state TEXT NOT NULL CHECK (rights_state IN ('SYNTHETIC', 'UNASSESSED', 'APPROVED', 'RESTRICTED', 'REJECTED')),
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (published_at IS NULL OR published_at >= first_observed_at)
        );

        CREATE TABLE racing_codes (
            code TEXT PRIMARY KEY CHECK (code IN ('THOROUGHBRED', 'HARNESS', 'GREYHOUND')),
            label TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE meetings (
            meeting_id TEXT PRIMARY KEY,
            code TEXT NOT NULL REFERENCES racing_codes(code),
            name TEXT NOT NULL,
            country TEXT NOT NULL DEFAULT 'AUS' CHECK (country = 'AUS'),
            scheduled_at TIMESTAMPTZ NOT NULL,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            source_receipt_id TEXT NOT NULL REFERENCES source_receipts(source_receipt_id),
            first_observed_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE race_revisions (
            race_revision_id BIGSERIAL PRIMARY KEY,
            race_id TEXT NOT NULL,
            meeting_id TEXT NOT NULL REFERENCES meetings(meeting_id),
            race_number INTEGER NOT NULL CHECK (race_number > 0),
            status TEXT NOT NULL CHECK (status IN ('SCHEDULED', 'ACCEPTANCES', 'FINAL_FIELDS', 'OFFICIAL', 'ABANDONED', 'POSTPONED')),
            field_revision TEXT NOT NULL,
            effective_from TIMESTAMPTZ NOT NULL,
            effective_to TIMESTAMPTZ,
            first_observed_at TIMESTAMPTZ NOT NULL,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            source_receipt_id TEXT NOT NULL REFERENCES source_receipts(source_receipt_id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (effective_to IS NULL OR effective_to > effective_from),
            UNIQUE (race_id, field_revision)
        );

        CREATE TABLE participants (
            participant_id TEXT PRIMARY KEY,
            code TEXT NOT NULL REFERENCES racing_codes(code),
            name TEXT NOT NULL,
            source_receipt_id TEXT NOT NULL REFERENCES source_receipts(source_receipt_id),
            first_observed_at TIMESTAMPTZ NOT NULL,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE entry_revisions (
            entry_revision_id BIGSERIAL PRIMARY KEY,
            entry_id TEXT NOT NULL,
            race_revision_id BIGINT NOT NULL REFERENCES race_revisions(race_revision_id),
            participant_id TEXT NOT NULL REFERENCES participants(participant_id),
            number INTEGER NOT NULL CHECK (number > 0),
            status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'SCRATCHED', 'RESERVE', 'COUPLED')),
            effective_from TIMESTAMPTZ NOT NULL,
            effective_to TIMESTAMPTZ,
            first_observed_at TIMESTAMPTZ NOT NULL,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            source_receipt_id TEXT NOT NULL REFERENCES source_receipts(source_receipt_id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (effective_to IS NULL OR effective_to > effective_from)
        );

        CREATE TABLE forecast_archives (
            forecast_id TEXT PRIMARY KEY,
            race_id TEXT NOT NULL,
            field_revision TEXT NOT NULL,
            cutoff_at TIMESTAMPTZ NOT NULL,
            model_version TEXT NOT NULL,
            manifest_sha256 TEXT NOT NULL CHECK (length(manifest_sha256) = 64),
            probabilities JSONB NOT NULL,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE selection_journal (
            selection_id TEXT PRIMARY KEY,
            race_id TEXT NOT NULL,
            entry_id TEXT,
            selection_type TEXT NOT NULL CHECK (selection_type IN ('WIN', 'PLACE', 'PASS')),
            rationale TEXT NOT NULL,
            forecast_id TEXT REFERENCES forecast_archives(forecast_id),
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE OR REPLACE FUNCTION reject_immutable_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'append-only table % cannot be updated or deleted', TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER source_receipts_append_only BEFORE UPDATE OR DELETE ON source_receipts
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER race_revisions_append_only BEFORE UPDATE OR DELETE ON race_revisions
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER entry_revisions_append_only BEFORE UPDATE OR DELETE ON entry_revisions
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER forecast_archives_append_only BEFORE UPDATE OR DELETE ON forecast_archives
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER selection_journal_append_only BEFORE UPDATE OR DELETE ON selection_journal
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();

        CREATE INDEX meetings_code_scheduled_idx ON meetings (code, scheduled_at, meeting_id);
        CREATE INDEX race_revisions_meeting_idx ON race_revisions (meeting_id, race_number, effective_from DESC);
        CREATE INDEX race_revisions_race_asof_idx ON race_revisions (race_id, effective_from DESC, effective_to);
        CREATE INDEX entry_revisions_race_idx ON entry_revisions (race_revision_id, number);
        CREATE INDEX forecast_archives_race_cutoff_idx ON forecast_archives (race_id, cutoff_at DESC);
        CREATE INDEX selection_journal_created_idx ON selection_journal (created_at DESC, selection_id);

        INSERT INTO racing_codes (code, label) VALUES
            ('THOROUGHBRED', 'Thoroughbred'),
            ('HARNESS', 'Harness'),
            ('GREYHOUND', 'Greyhound')
        ON CONFLICT (code) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS selection_journal_append_only ON selection_journal;
        DROP TRIGGER IF EXISTS forecast_archives_append_only ON forecast_archives;
        DROP TRIGGER IF EXISTS entry_revisions_append_only ON entry_revisions;
        DROP TRIGGER IF EXISTS race_revisions_append_only ON race_revisions;
        DROP TRIGGER IF EXISTS source_receipts_append_only ON source_receipts;
        DROP FUNCTION IF EXISTS reject_immutable_mutation();
        DROP TABLE IF EXISTS selection_journal;
        DROP TABLE IF EXISTS forecast_archives;
        DROP TABLE IF EXISTS entry_revisions;
        DROP TABLE IF EXISTS participants;
        DROP TABLE IF EXISTS race_revisions;
        DROP TABLE IF EXISTS meetings;
        DROP TABLE IF EXISTS racing_codes;
        DROP TABLE IF EXISTS source_receipts;
        DROP TABLE IF EXISTS schema_migration_checksums;
        """
    )
