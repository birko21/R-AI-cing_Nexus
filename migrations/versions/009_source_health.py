"""Add append-only source health events.

Revision ID: 009_source_health
Revises: 008_scraped_provenance
"""
from alembic import op

revision = "009_source_health"
down_revision = "008_scraped_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE source_health_events (
            event_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            checked_at TIMESTAMPTZ NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('HEALTHY', 'DEGRADED', 'DISABLED')),
            signal_kind TEXT,
            severity TEXT CHECK (severity IS NULL OR severity IN ('WARNING', 'CRITICAL')),
            detail TEXT NOT NULL,
            capabilities_disabled BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TRIGGER source_health_events_append_only BEFORE UPDATE OR DELETE ON source_health_events
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX source_health_events_source_checked_idx ON source_health_events (source_id, checked_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS source_health_events_append_only ON source_health_events;
        DROP TABLE IF EXISTS source_health_events;
        """
    )
