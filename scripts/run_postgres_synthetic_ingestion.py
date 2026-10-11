"""Run the synthetic ingestion worker against the disposable PostgreSQL store."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from sqlalchemy import create_engine


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.betfair_mock import SyntheticBetfairExchangeAdapter  # noqa: E402
from app.database_safety import validate_disposable_database_url  # noqa: E402
from app.ingestion import PostgresIngestionStore, SyntheticIngestionWorker  # noqa: E402
from app.providers import ContractedProviderAdapter  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthetic-only ingestion against disposable PostgreSQL")
    parser.add_argument("--code", choices=("THOROUGHBRED", "HARNESS", "GREYHOUND"), action="append", dest="codes")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--replay-id", default="postgres-smoke")
    parser.add_argument("--worker-id", default="synthetic-postgres-local-worker")
    args = parser.parse_args()
    try:
        validate_disposable_database_url()
    except ValueError as exc:
        raise SystemExit(f"DATABASE TARGET REJECTED: {exc}") from exc
    database_url = os.environ["DATABASE_URL"]
    engine = create_engine(database_url)
    with engine.begin() as connection:
        worker = SyntheticIngestionWorker(
            ContractedProviderAdapter(SyntheticBetfairExchangeAdapter()),
            store=PostgresIngestionStore(connection),
            worker_id=args.worker_id,
        )
        for code in args.codes or ("THOROUGHBRED", "HARNESS", "GREYHOUND"):
            worker.enqueue(code=code, page_size=args.page_size, replay_id=args.replay_id)
        summary = worker.run_until_idle()
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
