from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.walk_forward import RaceObservation, build_walk_forward_splits, split_manifest  # noqa: E402


FIXTURE = ROOT / "fixtures" / "synthetic" / "fixture.json"
OUTPUT = ROOT / "fixtures" / "synthetic" / "walk_forward_v1.json"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest() -> dict[str, object]:
    fixture = load_json(FIXTURE)
    collections = fixture["collections"]
    assert isinstance(collections, dict)
    races = collections["races"]
    assert isinstance(races, list)
    observations = tuple(RaceObservation(race["race_id"], datetime.fromisoformat(race["scheduled_at"].replace("Z", "+00:00")), race["code"]) for race in races)
    folds = build_walk_forward_splits(
        observations, initial_train_end=datetime(2026, 1, 15, 4, tzinfo=timezone.utc),
        initial_train_start=datetime(2026, 1, 15, 3, tzinfo=timezone.utc),
        calibration_duration=timedelta(hours=1), test_duration=timedelta(hours=1), step=timedelta(hours=1),
    )
    manifest = split_manifest(folds)
    manifest.update({
        "fixture_id": fixture["fixture_id"],
        "coverage_note": "The fixed demo fixture has one calendar day; no pre-demo training races are fabricated.",
        "fixture_race_count": len(observations),
    })
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_manifest()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("SPLIT MANIFEST CHECK FAILED: generated content differs")
    print(f"SPLIT MANIFEST VALID: folds={len(expected['folds'])} fixture_races={expected['fixture_race_count']}")


if __name__ == "__main__":
    main()
