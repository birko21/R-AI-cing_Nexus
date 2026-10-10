"""Add append-only paper scenario ledger.

Revision ID: 013_paper_ledger
Revises: 012_market_runner_status
"""
from alembic import op

revision = "013_paper_ledger"
down_revision = "012_market_runner_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE paper_positions (
            position_id TEXT PRIMARY KEY,
            selection_id TEXT NOT NULL,
            requested_stake NUMERIC NOT NULL CHECK (requested_stake > 0),
            matched_stake NUMERIC NOT NULL CHECK (matched_stake >= 0),
            price NUMERIC NOT NULL CHECK (price >= 1),
            liquidity NUMERIC CHECK (liquidity IS NULL OR liquidity >= 0),
            fill_status TEXT NOT NULL CHECK (fill_status IN ('FILLED', 'PARTIAL', 'UNFILLED', 'SCRATCHED')),
            fee NUMERIC NOT NULL CHECK (fee >= 0),
            exposure NUMERIC NOT NULL CHECK (exposure >= 0),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE paper_settlements (
            position_id TEXT PRIMARY KEY REFERENCES paper_positions(position_id),
            outcome TEXT NOT NULL CHECK (outcome IN ('WIN', 'LOSS', 'VOID', 'DEAD_HEAT', 'SCRATCHED')),
            matched_stake NUMERIC NOT NULL CHECK (matched_stake >= 0),
            gross_profit NUMERIC NOT NULL,
            commission NUMERIC NOT NULL CHECK (commission >= 0),
            fee NUMERIC NOT NULL CHECK (fee >= 0),
            removal_factor NUMERIC NOT NULL CHECK (removal_factor BETWEEN 0 AND 1),
            dead_heat_places INTEGER NOT NULL CHECK (dead_heat_places > 0),
            net_result NUMERIC NOT NULL,
            guaranteed BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TRIGGER paper_positions_append_only BEFORE UPDATE OR DELETE ON paper_positions
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER paper_settlements_append_only BEFORE UPDATE OR DELETE ON paper_settlements
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS paper_settlements_append_only ON paper_settlements;
        DROP TRIGGER IF EXISTS paper_positions_append_only ON paper_positions;
        DROP TABLE IF EXISTS paper_settlements;
        DROP TABLE IF EXISTS paper_positions;
        """
    )
