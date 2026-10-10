from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.thoroughbred_features import ThoroughbredFact, materialize_thoroughbred_features  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "thoroughbred_features_v1.json"
CUTOFF = datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc)


def build_fixture() -> dict[str, object]:
    snapshot = materialize_thoroughbred_features(
        race_id="race-1", participant_id="p1", cutoff=CUTOFF, target_class="BM", target_distance=1200,
        target_track_going="GOOD4", facts=[ThoroughbredFact("p1", datetime(2025, 12, 1, tzinfo=timezone.utc), "receipt-tb-1", "BM", 1200, "GOOD4", 3, 57.0, 81.0, 34.2)],
    )
    return {
        "schema_version": "thoroughbred-features-v1", "record": snapshot.to_dict(), "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Descriptive specialist feature evidence only; no causal attribution, validated model or live source claim.",
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
        raise SystemExit("THOROUGHBRED FEATURE FIXTURE CHECK FAILED: generated content differs")
    print(f"THOROUGHBRED FEATURE FIXTURE VALID: features={len(expected['record']['features'])} attribution={expected['record']['attribution_status']}")


if __name__ == "__main__":
    main()
