from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.greyhound_features import GreyhoundFact, activate_reserve, materialize_greyhound_features  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "greyhound_features_v1.json"


def build_fixture() -> dict[str, object]:
    cutoff = datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc)
    original = materialize_greyhound_features(
        race_id="race-1", participant_id="p1", cutoff=cutoff,
        facts=(GreyhoundFact("p1", datetime(2025, 12, 1, tzinfo=timezone.utc), "receipt-g-1", 4, 5.8, 0.7, "wide", "G5", "none", "none"),),
    )
    updated = activate_reserve(original, GreyhoundFact("p1", cutoff, "receipt-g-reserve", 1, 5.2, 0.9, "inside", "G4", "crowded", "checked"), authorised_features=frozenset({"box", "trouble"}))
    return {
        "schema_version": "greyhound-features-v1", "original": original.to_dict(), "reserve_activation": updated.to_dict(),
        "fictional": True, "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Greyhound specialist and authorised-recompute evidence only; no causal, validated or wagering claim.",
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
        raise SystemExit("GREYHOUND FEATURE FIXTURE CHECK FAILED: generated content differs")
    print(f"GREYHOUND FEATURE FIXTURE VALID: recomputed={expected['reserve_activation']['recomputed_features']}")


if __name__ == "__main__":
    main()
