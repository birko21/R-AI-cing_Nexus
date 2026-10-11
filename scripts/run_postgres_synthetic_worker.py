"""Run a long-lived synthetic ingestion consumer against disposable PostgreSQL."""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import sys
from threading import Event

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.betfair_mock import SyntheticBetfairExchangeAdapter  # noqa: E402
from app.database_safety import validate_disposable_database_url  # noqa: E402
from app.ingestion import IngestionJob, PostgresIngestionStore, SyntheticIngestionWorker  # noqa: E402
from app.providers import ContractedProviderAdapter  # noqa: E402
from app.worker_runtime import WorkerLoopSummary, run_until_stopped  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Consume synthetic ingestion jobs from disposable PostgreSQL until stopped"
    )
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    parser.add_argument("--max-jobs", type=int, help="stop after processing this many jobs")
    parser.add_argument("--once", action="store_true", help="poll once and exit; useful for smoke tests")
    parser.add_argument("--worker-id", default="synthetic-postgres-local-worker")
    parser.add_argument("--lease-seconds", type=int, default=60)
    return parser


@contextmanager
def _signal_shutdown(stop_event: Event) -> Iterator[None]:
    """Install cooperative shutdown handlers and restore the caller's handlers."""

    previous: dict[int, signal.Handlers] = {}

    def request_shutdown(_signum: int, _frame: object) -> None:
        stop_event.set()

    for signum in (signal.SIGINT, signal.SIGTERM):
        previous[signum] = signal.getsignal(signum)
        signal.signal(signum, request_shutdown)
    try:
        yield
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def run_worker(
    engine: Engine,
    *,
    worker_id: str,
    lease_seconds: int,
    poll_seconds: float,
    stop_event: Event,
    max_jobs: int | None = None,
) -> WorkerLoopSummary:
    """Consume one bounded job per transaction until the loop exits."""

    adapter = ContractedProviderAdapter(SyntheticBetfairExchangeAdapter())

    def step() -> IngestionJob | None:
        with engine.begin() as connection:
            worker = SyntheticIngestionWorker(
                adapter,
                store=PostgresIngestionStore(connection),
                worker_id=worker_id,
                lease_seconds=lease_seconds,
            )
            return worker.run_next()

    return run_until_stopped(
        step,
        stop_event=stop_event,
        poll_seconds=poll_seconds,
        max_jobs=max_jobs,
    )


def main() -> None:
    args = _parser().parse_args()
    if args.once and args.max_jobs is not None:
        raise SystemExit("use either --once or --max-jobs, not both")
    max_jobs = 1 if args.once else args.max_jobs
    try:
        validate_disposable_database_url()
    except ValueError as exc:
        raise SystemExit(f"DATABASE TARGET REJECTED: {exc}") from exc

    stop_event = Event()
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with _signal_shutdown(stop_event):
            summary = run_worker(
                engine,
                worker_id=args.worker_id,
                lease_seconds=args.lease_seconds,
                poll_seconds=args.poll_seconds,
                stop_event=stop_event,
                max_jobs=max_jobs,
            )
    finally:
        engine.dispose()
    print(json.dumps(summary.__dict__, indent=2))


if __name__ == "__main__":
    main()
