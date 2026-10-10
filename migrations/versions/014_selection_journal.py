"""Add immutable personal selections and correction addenda.

Revision ID: 014_selection_journal
Revises: 013_paper_ledger
"""
from alembic import op

revision = "014_selection_journal"
down_revision = "013_paper_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE personal_selections (
            selection_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            race_id TEXT NOT NULL,
            field_revision TEXT NOT NULL,
            entry_id TEXT,
            selection_type TEXT NOT NULL CHECK (selection_type IN ('WIN', 'PLACE', 'PASS')),
            rationale TEXT NOT NULL,
            forecast_id TEXT,
            quote_id TEXT,
            created_at TIMESTAMPTZ NOT NULL,
            decision_time TIMESTAMPTZ NOT NULL,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            CHECK (selection_type = 'PASS' OR entry_id IS NOT NULL)
        );

        CREATE TABLE selection_addenda (
            addendum_id TEXT PRIMARY KEY,
            selection_id TEXT NOT NULL REFERENCES personal_selections(selection_id),
            user_id TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        );

        CREATE TRIGGER personal_selections_append_only BEFORE UPDATE OR DELETE ON personal_selections
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER selection_addenda_append_only BEFORE UPDATE OR DELETE ON selection_addenda
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX personal_selections_user_created_idx ON personal_selections (user_id, created_at DESC);
        CREATE INDEX selection_addenda_selection_created_idx ON selection_addenda (selection_id, created_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS selection_addenda_append_only ON selection_addenda;
        DROP TRIGGER IF EXISTS personal_selections_append_only ON personal_selections;
        DROP TABLE IF EXISTS selection_addenda;
        DROP TABLE IF EXISTS personal_selections;
        """
    )
