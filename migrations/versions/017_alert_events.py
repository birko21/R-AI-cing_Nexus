"""Add append-only source-linked change events and deduplicated alerts.

Revision ID: 017_alert_events
Revises: 016_watchlists
"""
from alembic import op

revision = "017_alert_events"
down_revision = "016_watchlists"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE change_events (
            event_id TEXT PRIMARY KEY,
            watch_id TEXT NOT NULL REFERENCES watch_targets(watch_id),
            source_system TEXT NOT NULL,
            source_receipt_id TEXT NOT NULL,
            observed_at TIMESTAMPTZ NOT NULL,
            validity TEXT NOT NULL CHECK (validity IN ('CONFIRMED', 'UNCONFIRMED')),
            material BOOLEAN NOT NULL,
            suppression_key TEXT NOT NULL,
            cause TEXT NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL CHECK (expires_at > observed_at)
        );

        CREATE TABLE alerts (
            alert_id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL REFERENCES change_events(event_id),
            watch_id TEXT NOT NULL REFERENCES watch_targets(watch_id),
            source_system TEXT NOT NULL,
            source_receipt_id TEXT NOT NULL,
            observed_at TIMESTAMPTZ NOT NULL,
            suppression_key TEXT NOT NULL,
            cause TEXT NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'EXPIRED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TRIGGER change_events_append_only BEFORE UPDATE OR DELETE ON change_events
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER alerts_append_only BEFORE UPDATE OR DELETE ON alerts
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE UNIQUE INDEX alerts_active_suppression_idx ON alerts (suppression_key) WHERE status = 'ACTIVE';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS alerts_active_suppression_idx;
        DROP TRIGGER IF EXISTS alerts_append_only ON alerts;
        DROP TRIGGER IF EXISTS change_events_append_only ON change_events;
        DROP TABLE IF EXISTS alerts;
        DROP TABLE IF EXISTS change_events;
        """
    )
