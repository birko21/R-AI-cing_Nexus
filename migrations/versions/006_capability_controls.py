"""Add source capability and retention controls.

Revision ID: 006_capability_controls
Revises: 005_raw_envelopes_quarantine
"""
from alembic import op

revision = "006_capability_controls"
down_revision = "005_raw_envelopes_quarantine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE source_capability_controls (
            source_id TEXT PRIMARY KEY,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            rights_state TEXT NOT NULL CHECK (rights_state IN ('SYNTHETIC', 'UNASSESSED', 'APPROVED', 'RESTRICTED', 'REJECTED')),
            approved_capabilities TEXT[] NOT NULL DEFAULT '{}',
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            kill_switch_reason TEXT,
            retention_until TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX source_capability_controls_enabled_idx ON source_capability_controls (enabled, retention_until);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS source_capability_controls;")
