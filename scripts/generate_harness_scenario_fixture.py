from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.harness_scenarios import HarnessFact, build_harness_scenario  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "harness_scenarios_v1.json"


def build_fixture() -> dict[str, object]:
    cutoff = datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc)
    scenario = build_harness_scenario(
        scenario_id="scenario-1", participant_id="p1", cutoff=cutoff,
        facts=(HarnessFact("p1", datetime(2025, 12, 1, tzinfo=timezone.utc), "receipt-h-1", "MOBILE", 1, 3, "MIDFIELD", 31.2, "settles behind leader"),),
    )
    unavailable = build_harness_scenario(scenario_id="scenario-empty", participant_id="p1", cutoff=cutoff, facts=())
    return {
        "schema_version": "harness-scenarios-v1", "experimental": scenario.to_dict(), "not_available": unavailable.to_dict(),
        "fictional": True, "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Experimental uncalibrated scenario evidence only; no causal, validated or wagering claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("HARNESS SCENARIO FIXTURE CHECK FAILED: generated content differs")
    print(f"HARNESS SCENARIO FIXTURE VALID: experimental={expected['experimental']['status']} unavailable={expected['not_available']['status']}")


if __name__ == "__main__":
    main()
