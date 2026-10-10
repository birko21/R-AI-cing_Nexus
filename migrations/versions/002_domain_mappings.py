"""Add immutable market-selection mappings.

Revision ID: 002_domain_mappings
Revises: 001_offline_mvp
"""
from alembic import op

revision = "002_domain_mappings"
down_revision = "001_offline_mvp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE market_selection_mappings (
            mapping_id TEXT PRIMARY KEY,
            code TEXT NOT NULL CHECK (code IN ('THOROUGHBRED', 'HARNESS', 'GREYHOUND')),
            race_id TEXT NOT NULL,
            field_revision TEXT NOT NULL,
            entry_id TEXT NOT NULL,
            market_source TEXT NOT NULL,
            market_id TEXT NOT NULL,
            selection_id TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (length(trim(entry_id)) > 0),
            CHECK (length(trim(market_id)) > 0),
            CHECK (length(trim(selection_id)) > 0),
            UNIQUE (market_source, market_id, selection_id)
        );

        CREATE TRIGGER market_selection_mappings_append_only BEFORE UPDATE OR DELETE ON market_selection_mappings
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX market_selection_mappings_entry_idx ON market_selection_mappings (code, race_id, field_revision, entry_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS market_selection_mappings_append_only ON market_selection_mappings;
        DROP TABLE IF EXISTS market_selection_mappings;
        """
    )
