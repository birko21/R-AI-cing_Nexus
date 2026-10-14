"""Verify the durable ingestion job schema after migrations have run."""

from __future__ import annotations

import os

from sqlalchemy import create_engine, text


EXPECTED_COLUMNS = {
    "job_id", "idempotency_key", "provider_id", "operation", "code", "cursor", "replay_id",
    "page_size", "attempt", "max_attempts", "status", "available_at", "lease_owner", "lease_until",
    "records_persisted", "records_skipped", "records_quarantined", "error", "created_at", "started_at",
    "finished_at", "continuation_job_id",
}


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL must be set")
    engine = create_engine(database_url)
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'ingestion_jobs'")
        )
        columns = {row[0] for row in rows}
    missing = sorted(EXPECTED_COLUMNS - columns)
    if missing:
        raise SystemExit(f"INGESTION SCHEMA INVALID: missing columns={missing}")
    print(f"INGESTION SCHEMA VALID: columns={len(columns)}")


if __name__ == "__main__":
    main()
