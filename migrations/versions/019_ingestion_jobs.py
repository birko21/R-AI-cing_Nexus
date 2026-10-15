"""Add durable ingestion job and lease state.

Revision ID: 019_ingestion_jobs
Revises: 018_responsible_controls
"""
from alembic import op

revision = "019_ingestion_jobs"
down_revision = "018_responsible_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ingestion_jobs (
            job_id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            provider_id TEXT NOT NULL,
            operation TEXT NOT NULL CHECK (operation IN ('LIST_MEETINGS', 'GET_RACES', 'GET_ENTRIES', 'GET_RESULTS', 'GET_MARKETS', 'ACCOUNT_METADATA_READ')),
            code TEXT NOT NULL CHECK (code IN ('THOROUGHBRED', 'HARNESS', 'GREYHOUND')),
            cursor TEXT,
            replay_id TEXT NOT NULL,
            page_size INTEGER NOT NULL CHECK (page_size BETWEEN 1 AND 100),
            attempt INTEGER NOT NULL DEFAULT 0 CHECK (attempt >= 0),
            max_attempts INTEGER NOT NULL DEFAULT 3 CHECK (max_attempts BETWEEN 1 AND 10),
            status TEXT NOT NULL CHECK (status IN ('QUEUED', 'RUNNING', 'RETRYABLE', 'SUCCEEDED', 'FAILED', 'QUARANTINED', 'SKIPPED')),
            available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            lease_owner TEXT,
            lease_until TIMESTAMPTZ,
            records_persisted INTEGER NOT NULL DEFAULT 0 CHECK (records_persisted >= 0),
            records_skipped INTEGER NOT NULL DEFAULT 0 CHECK (records_skipped >= 0),
            records_quarantined INTEGER NOT NULL DEFAULT 0 CHECK (records_quarantined >= 0),
            error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            continuation_job_id TEXT REFERENCES ingestion_jobs(job_id),
            CHECK (attempt <= max_attempts),
            CHECK (status <> 'RUNNING' OR (lease_owner IS NOT NULL AND lease_until IS NOT NULL)),
            CHECK (status = 'RUNNING' OR (lease_owner IS NULL AND lease_until IS NULL))
        );

        CREATE INDEX ingestion_jobs_claim_idx
            ON ingestion_jobs (status, available_at, created_at, job_id);
        CREATE INDEX ingestion_jobs_lease_idx
            ON ingestion_jobs (lease_until) WHERE status = 'RUNNING';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ingestion_jobs_lease_idx;
        DROP INDEX IF EXISTS ingestion_jobs_claim_idx;
        DROP TABLE IF EXISTS ingestion_jobs;
        """
    )
