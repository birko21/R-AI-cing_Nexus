"""Add stable watchlist targets and append-only lifecycle events.

Revision ID: 016_watchlists
Revises: 015_official_results
"""
from alembic import op

revision = "016_watchlists"
down_revision = "015_official_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE watch_targets (
            watch_id TEXT PRIMARY KEY,
            entity_id TEXT NOT NULL,
            kind TEXT NOT NULL CHECK (kind IN ('RUNNER', 'RACE')),
            code TEXT NOT NULL CHECK (code IN ('THOROUGHBRED', 'HARNESS', 'GREYHOUND')),
            source_system TEXT NOT NULL,
            source_id TEXT NOT NULL,
            name TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN ('ACTIVE', 'PAUSED', 'REMOVED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE watch_events (
            event_id TEXT PRIMARY KEY,
            watch_id TEXT NOT NULL REFERENCES watch_targets(watch_id),
            kind TEXT NOT NULL CHECK (kind IN ('CREATED', 'IDENTITY_CHANGED', 'SOURCE_CHANGED', 'PAUSED', 'RESUMED', 'REMOVED')),
            observed_at TIMESTAMPTZ NOT NULL,
            source_system TEXT NOT NULL,
            source_id TEXT NOT NULL,
            name TEXT NOT NULL,
            detail TEXT NOT NULL
        );

        CREATE TRIGGER watch_targets_append_only BEFORE UPDATE OR DELETE ON watch_targets
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER watch_events_append_only BEFORE UPDATE OR DELETE ON watch_events
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX watch_events_target_observed_idx ON watch_events (watch_id, observed_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS watch_events_append_only ON watch_events;
        DROP TRIGGER IF EXISTS watch_targets_append_only ON watch_targets;
        DROP TABLE IF EXISTS watch_events;
        DROP TABLE IF EXISTS watch_targets;
        """
    )
