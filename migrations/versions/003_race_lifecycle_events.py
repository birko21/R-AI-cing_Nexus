"""Add immutable race lifecycle events.

Revision ID: 003_race_lifecycle_events
Revises: 002_domain_mappings
"""
from alembic import op

revision = "003_race_lifecycle_events"
down_revision = "002_domain_mappings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE race_lifecycle_events (
            event_id TEXT PRIMARY KEY,
            race_id TEXT NOT NULL,
            code TEXT NOT NULL CHECK (code IN ('THOROUGHBRED', 'HARNESS', 'GREYHOUND')),
            event_type TEXT NOT NULL CHECK (event_type IN ('ACCEPTANCES', 'FINAL_FIELDS', 'SCRATCHING', 'RESERVE', 'POSTPONEMENT', 'OFFICIAL_RESULT', 'ABANDONED', 'CORRECTION')),
            status TEXT NOT NULL CHECK (status IN ('SCHEDULED', 'ACCEPTANCES', 'FINAL_FIELDS', 'OFFICIAL', 'ABANDONED', 'POSTPONED')),
            field_revision TEXT NOT NULL,
            observed_at TIMESTAMPTZ NOT NULL,
            effective_at TIMESTAMPTZ NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            source_receipt_id TEXT REFERENCES source_receipts(source_receipt_id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TRIGGER race_lifecycle_events_append_only BEFORE UPDATE OR DELETE ON race_lifecycle_events
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX race_lifecycle_events_order_idx ON race_lifecycle_events (race_id, observed_at, event_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS race_lifecycle_events_append_only ON race_lifecycle_events;
        DROP TABLE IF EXISTS race_lifecycle_events;
        """
    )
