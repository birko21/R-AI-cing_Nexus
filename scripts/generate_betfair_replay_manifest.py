"""Validate the deterministic synthetic Betfair replay manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.betfair_mock import (  # noqa: E402
    build_synthetic_betfair_replay_manifest,
    reconcile_synthetic_betfair_replay_manifest,
)


OUTPUT = ROOT / "fixtures" / "synthetic" / "betfair_market_replay_manifest_v1.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_synthetic_betfair_replay_manifest()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists():
        raise SystemExit("BETFAIR REPLAY MANIFEST CHECK FAILED: generated content differs")
    observed = json.loads(args.output.read_text(encoding="utf-8"))
    report = reconcile_synthetic_betfair_replay_manifest(observed)
    if report.status != "MATCH":
        raise SystemExit(f"BETFAIR REPLAY MANIFEST CHECK FAILED: {report.to_dict()}")
    print(f"BETFAIR REPLAY MANIFEST VALID: pages={report.observed_pages} records={report.observed_records}")


if __name__ == "__main__":
    main()
