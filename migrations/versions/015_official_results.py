"""Add immutable official result revisions and selection reconciliations.

Revision ID: 015_official_results
Revises: 014_selection_journal
"""
from alembic import op

revision = "015_official_results"
down_revision = "014_selection_journal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE official_result_revisions (
            result_id TEXT PRIMARY KEY,
            race_id TEXT NOT NULL,
            field_revision TEXT NOT NULL,
            source_receipt_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('PENDING', 'OFFICIAL', 'CORRECTED')),
            observed_at TIMESTAMPTZ NOT NULL,
            official_at TIMESTAMPTZ,
            placings JSONB NOT NULL,
            dead_heat_groups JSONB NOT NULL DEFAULT '[]'::jsonb,
            scratched_entries TEXT[] NOT NULL DEFAULT '{}',
            correction_of TEXT REFERENCES official_result_revisions(result_id),
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (status = 'PENDING' OR official_at IS NOT NULL),
            CHECK (status <> 'CORRECTED' OR correction_of IS NOT NULL)
        );

        CREATE TABLE selection_reconciliations (
            selection_id TEXT NOT NULL REFERENCES personal_selections(selection_id),
            result_id TEXT NOT NULL REFERENCES official_result_revisions(result_id),
            outcome TEXT NOT NULL CHECK (outcome IN ('PENDING', 'PASS', 'WIN', 'PLACE', 'LOSS', 'SCRATCHED', 'DEAD_HEAT', 'VOID')),
            reconciled_at TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (selection_id, result_id)
        );

        CREATE TRIGGER official_result_revisions_append_only BEFORE UPDATE OR DELETE ON official_result_revisions
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER selection_reconciliations_append_only BEFORE UPDATE OR DELETE ON selection_reconciliations
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS selection_reconciliations_append_only ON selection_reconciliations;
        DROP TRIGGER IF EXISTS official_result_revisions_append_only ON official_result_revisions;
        DROP TABLE IF EXISTS selection_reconciliations;
        DROP TABLE IF EXISTS official_result_revisions;
        """
    )
