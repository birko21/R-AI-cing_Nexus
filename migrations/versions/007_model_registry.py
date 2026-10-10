"""Add immutable model registry and assurance events.

Revision ID: 007_model_registry
Revises: 006_capability_controls
"""
from alembic import op

revision = "007_model_registry"
down_revision = "006_capability_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE model_artifacts (
            artifact_id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            model_version TEXT NOT NULL,
            artifact_sha256 TEXT NOT NULL CHECK (length(artifact_sha256) = 64),
            feature_schema_version TEXT NOT NULL,
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            model_status TEXT NOT NULL CHECK (model_status IN ('ILLUSTRATIVE_NOT_VALIDATED', 'EXPERIMENTAL', 'VALIDATED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE model_evaluations (
            evaluation_id TEXT PRIMARY KEY,
            artifact_id TEXT NOT NULL REFERENCES model_artifacts(artifact_id),
            split_manifest_hash TEXT NOT NULL CHECK (length(split_manifest_hash) = 64),
            metrics JSONB NOT NULL,
            sample_count INTEGER NOT NULL CHECK (sample_count >= 0),
            data_mode TEXT NOT NULL CHECK (data_mode IN ('SYNTHETIC_ONLY', 'SCRAPED_PUBLIC', 'LICENSED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE model_assurance_events (
            assurance_id TEXT PRIMARY KEY,
            evaluation_id TEXT NOT NULL REFERENCES model_evaluations(evaluation_id),
            outcome TEXT NOT NULL CHECK (outcome IN ('PENDING', 'PASS', 'FAIL')),
            reviewer TEXT NOT NULL,
            notes TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE model_registry_decisions (
            decision_id TEXT PRIMARY KEY,
            artifact_id TEXT NOT NULL REFERENCES model_artifacts(artifact_id),
            status TEXT NOT NULL CHECK (status IN ('INSUFFICIENT EVIDENCE', 'SHADOW', 'HOLD', 'BLOCK', 'CHAMPION')),
            decision_reason TEXT NOT NULL,
            approved_by TEXT,
            evaluation_id TEXT REFERENCES model_evaluations(evaluation_id),
            assurance_id TEXT REFERENCES model_assurance_events(assurance_id),
            manual_approval BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (status <> 'CHAMPION' OR (manual_approval = TRUE AND approved_by IS NOT NULL AND assurance_id IS NOT NULL))
        );

        CREATE TRIGGER model_artifacts_append_only BEFORE UPDATE OR DELETE ON model_artifacts
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER model_evaluations_append_only BEFORE UPDATE OR DELETE ON model_evaluations
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER model_assurance_events_append_only BEFORE UPDATE OR DELETE ON model_assurance_events
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE TRIGGER model_registry_decisions_append_only BEFORE UPDATE OR DELETE ON model_registry_decisions
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
        CREATE INDEX model_evaluations_artifact_idx ON model_evaluations (artifact_id, created_at DESC);
        CREATE INDEX model_registry_decisions_status_idx ON model_registry_decisions (status, created_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS model_registry_decisions_append_only ON model_registry_decisions;
        DROP TRIGGER IF EXISTS model_assurance_events_append_only ON model_assurance_events;
        DROP TRIGGER IF EXISTS model_evaluations_append_only ON model_evaluations;
        DROP TRIGGER IF EXISTS model_artifacts_append_only ON model_artifacts;
        DROP TABLE IF EXISTS model_registry_decisions;
        DROP TABLE IF EXISTS model_assurance_events;
        DROP TABLE IF EXISTS model_evaluations;
        DROP TABLE IF EXISTS model_artifacts;
        """
    )

