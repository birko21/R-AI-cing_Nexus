"""Run the offline synthetic ingestion worker and print a JSON summary."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.betfair_mock import SyntheticBetfairExchangeAdapter  # noqa: E402
from app.ingestion import SyntheticIngestionWorker  # noqa: E402
from app.providers import ContractedProviderAdapter  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic-only ingestion worker")
    parser.add_argument(
        "--code",
        choices=("THOROUGHBRED", "HARNESS", "GREYHOUND"),
        action="append",
        dest="codes",
        help="code to ingest; repeat for multiple codes (default: all three)",
    )
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--replay-id", default="cli-run")
    args = parser.parse_args()

    worker = SyntheticIngestionWorker(ContractedProviderAdapter(SyntheticBetfairExchangeAdapter()))
    for code in args.codes or ("THOROUGHBRED", "HARNESS", "GREYHOUND"):
        worker.enqueue(code=code, page_size=args.page_size, replay_id=args.replay_id)
    summary = worker.run_until_idle()
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
