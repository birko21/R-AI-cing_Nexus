from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.form_heuristic import FormRace, FormRun, FormRunner, build_b1_forecast  # noqa: E402


WATERMARK = "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE"
OUTPUT = ROOT / "fixtures" / "synthetic" / "forecasts_b1.json"
FIXTURE = ROOT / "fixtures" / "synthetic" / "fixture.json"
FIXTURE_MANIFEST = ROOT / "fixtures" / "synthetic" / "manifest.json"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest() -> dict[str, object]:
    fixture = load_json(FIXTURE)
    fixture_manifest = load_json(FIXTURE_MANIFEST)
    collections = fixture["collections"]
    assert isinstance(collections, dict)
    races = collections["races"]
    entries = collections["entries"]
    runs = collections["historical_runs"]
    scratchings = collections["scratchings"]
    reserves = collections["reserves"]
    assert isinstance(races, list)
    assert isinstance(entries, list)
    assert isinstance(runs, list)
    assert isinstance(scratchings, list)
    assert isinstance(reserves, list)
    fixture_files = fixture_manifest["files"]
    assert isinstance(fixture_files, dict)
    fixture_file = fixture_files["fixture.json"]
    assert isinstance(fixture_file, dict)
    fixture_checksum = fixture_file["sha256"]
    assert isinstance(fixture_checksum, str)

    scratch_ids = {(item["race_id"], item["entry_id"]) for item in scratchings}
    reserve_ids = {(item["race_id"], item["entry_id"]) for item in reserves}
    runs_by_participant: dict[str, list[FormRun]] = {}
    for run in runs:
        runs_by_participant.setdefault(run["participant_id"], []).append(
            FormRun(
                participant_id=run["participant_id"],
                observed_at=datetime.fromisoformat(f"{run['run_date']}T00:00:00+00:00"),
                distance=run["distance"],
                finish_position=run["finish_position"],
            )
        )

    forecasts: list[dict[str, object]] = []
    for race in races:
        race_id = race["race_id"]
        race_entries = [item for item in entries if item["race_id"] == race_id]
        runners: list[FormRunner] = []
        for entry in race_entries:
            key = (race_id, entry["entry_id"])
            status = "SCRATCHED" if key in scratch_ids else "RESERVE" if key in reserve_ids else "ACTIVE"
            runners.append(
                FormRunner(
                    entry_id=entry["entry_id"], participant_id=entry["participant_id"], number=entry["number"],
                    status=status, eligible=status == "ACTIVE", runs=tuple(runs_by_participant[entry["participant_id"]]),
                )
            )
        scheduled_at = datetime.fromisoformat(str(race["scheduled_at"]).replace("Z", "+00:00"))
        target_distance = 1200 + (int(race["race_number"]) - 1) * 200
        form_race = FormRace(
            race_id=race_id, code=race["code"], field_revision=race["field_revision"], field_status=race["status"],
            target_distance=target_distance, runners=tuple(runners),
        )
        forecasts.append(
            build_b1_forecast(
                form_race, cutoff=scheduled_at - timedelta(minutes=30), manifest_checksum=fixture_checksum
            ).to_dict()
        )

    return {
        "schema_version": "ril-022-b1-v1",
        "fixture_id": fixture["fixture_id"],
        "source_fixture_sha256": fixture_checksum,
        "generated_at": "2026-01-15T00:00:00Z",
        "model": {
            "model_id": "B1_FORM_HEURISTIC",
            "model_version": "b1-form-v1",
            "model_status": "ILLUSTRATIVE_NOT_VALIDATED",
            "inputs": ["pre_cutoff_historical_runs", "target_distance", "field_membership"],
            "minimum_support": 2,
            "smoothing": 0.1,
            "data_mode": "SYNTHETIC_ONLY",
        },
        "forecasts": forecasts,
        "fictional": True,
        "watermark": WATERMARK,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_manifest()
    if args.write:
        write_json(args.output, expected)
    if not args.output.exists():
        raise SystemExit(f"B1 MANIFEST CHECK FAILED: missing {args.output}")
    actual = load_json(args.output)
    if actual != expected:
        raise SystemExit("B1 MANIFEST CHECK FAILED: generated content differs")
    ready = sum(item["status"] == "READY" for item in expected["forecasts"])
    print(f"B1 MANIFEST VALID: forecasts={len(expected['forecasts'])} ready={ready}")


if __name__ == "__main__":
    main()
