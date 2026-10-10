"""Add append-only responsible-use settings and annotation exports.

Revision ID: 018_responsible_controls
Revises: 017_alert_events
"""
from alembic import op

revision = "018_responsible_controls"
down_revision = "017_alert_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE responsible_use_settings (
            user_id TEXT PRIMARY KEY,
            paused BOOLEAN NOT NULL DEFAULT FALSE,
            quiet_hours_start TIME NOT NULL,
            quiet_hours_end TIME NOT NULL,
            max_session_seconds INTEGER NOT NULL CHECK (max_session_seconds > 0),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE annotation_exports (
            export_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            export_type TEXT NOT NULL CHECK (export_type = 'ANNOTATIONS_ONLY'),
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            raw_prices_included BOOLEAN NOT NULL DEFAULT FALSE,
            forecast_payloads_included BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TRIGGER annotation_exports_append_only BEFORE UPDATE OR DELETE ON annotation_exports
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS annotation_exports_append_only ON annotation_exports;
        DROP TABLE IF EXISTS annotation_exports;
        DROP TABLE IF EXISTS responsible_use_settings;
        """
    )
