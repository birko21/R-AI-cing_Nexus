"""Validate the deterministic synthetic Betfair replay manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.betfair_mock import build_synthetic_betfair_replay_manifest  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "betfair_market_replay_manifest_v1.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_synthetic_betfair_replay_manifest()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("BETFAIR REPLAY MANIFEST CHECK FAILED: generated content differs")
    print(f"BETFAIR REPLAY MANIFEST VALID: pages={len(expected['pages'])} records={expected['record_count']}")


if __name__ == "__main__":
    main()
