from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.features import HistoricalRunFact, materialize_feature_manifest, materialize_feature_snapshot  # noqa: E402


FIXTURE = ROOT / "fixtures" / "synthetic" / "fixture.json"
OUTPUT = ROOT / "fixtures" / "synthetic" / "features_v1.json"
CUTOFF = datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest() -> dict[str, object]:
    fixture = load_json(FIXTURE)
    collections = fixture["collections"]
    assert isinstance(collections, dict)
    entries = collections["entries"]
    runs = collections["historical_runs"]
    races = collections["races"]
    assert isinstance(entries, list)
    assert isinstance(runs, list)
    assert isinstance(races, list)
    race_by_id = {race["race_id"]: race for race in races}
    facts_by_participant: dict[str, list[HistoricalRunFact]] = {}
    for run in runs:
        fact = HistoricalRunFact(
            participant_id=run["participant_id"], code=run["code"],
            observed_at=datetime.fromisoformat(f"{run['run_date']}T00:00:00+00:00"),
            distance=run["distance"], finish_position=run["finish_position"], source_receipt_id=run["source_receipt_id"],
        )
        facts_by_participant.setdefault(fact.participant_id, []).append(fact)
    snapshots = []
    for entry in entries:
        race = race_by_id[entry["race_id"]]
        snapshots.append(
            materialize_feature_snapshot(
                race_id=race["race_id"], participant_id=entry["participant_id"], code=entry["code"],
                cutoff=CUTOFF, target_distance=1200 + (int(race["race_number"]) - 1) * 200, facts=facts_by_participant[entry["participant_id"]],
            )
        )
    manifest = materialize_feature_manifest(snapshots)
    manifest.update({"fixture_id": fixture["fixture_id"], "cutoff": "2026-01-15T03:30:00Z"})
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
        raise SystemExit("FEATURE MANIFEST CHECK FAILED: generated content differs")
    print(f"FEATURE MANIFEST VALID: records={expected['record_count']} cutoff={expected['cutoff']}")


if __name__ == "__main__":
    main()
