from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.baseline import BaselineRace, BaselineRunner, build_b0_forecast  # noqa: E402


WATERMARK = "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE"
OUTPUT = ROOT / "fixtures" / "synthetic" / "forecasts_b0.json"
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
    scratchings = collections["scratchings"]
    reserves = collections["reserves"]
    edge_cases = collections["edge_cases"]
    assert isinstance(races, list)
    assert isinstance(entries, list)
    assert isinstance(scratchings, list)
    assert isinstance(reserves, list)
    assert isinstance(edge_cases, list)
    fixture_files = fixture_manifest["files"]
    assert isinstance(fixture_files, dict)
    fixture_file = fixture_files["fixture.json"]
    assert isinstance(fixture_file, dict)
    fixture_checksum = fixture_file["sha256"]
    assert isinstance(fixture_checksum, str)

    scratch_ids = {(item["race_id"], item["entry_id"]) for item in scratchings}
    reserve_ids = {(item["race_id"], item["entry_id"]) for item in reserves}
    forecasts: list[dict[str, object]] = []
    for race in races:
        assert isinstance(race, dict)
        race_id = race["race_id"]
        assert isinstance(race_id, str)
        race_entries = [item for item in entries if item["race_id"] == race_id]
        runners: list[BaselineRunner] = []
        for entry in race_entries:
            entry_id = entry["entry_id"]
            key = (race_id, entry_id)
            status = "SCRATCHED" if key in scratch_ids else "RESERVE" if key in reserve_ids else "ACTIVE"
            runners.append(BaselineRunner(entry_id=entry_id, number=entry["number"], status=status, eligible=status == "ACTIVE"))
        scheduled_at = datetime.fromisoformat(str(race["scheduled_at"]).replace("Z", "+00:00"))
        baseline_race = BaselineRace(
            race_id=race_id,
            code=race["code"],
            field_revision=race["field_revision"],
            field_status=race["status"],
            runners=tuple(runners),
        )
        forecasts.append(
            build_b0_forecast(
                baseline_race,
                cutoff=scheduled_at - timedelta(minutes=30),
                manifest_checksum=fixture_checksum,
            ).to_dict()
        )

    reason_by_case = {
        "COUPLED_ENTRY": "COUPLED_ENTRY",
        "INCOMPLETE_FIELD": "INCOMPLETE_FIELD",
        "NO_RACING": "NOT_AVAILABLE",
        "DEAD_HEAT": "UNSUPPORTED_OUTCOME",
    }
    abstentions = [
        {
            "record_id": edge["record_id"],
            "code": edge["code"],
            "case": edge["case"],
            "status": "ABSTAIN" if edge["case"] != "NO_RACING" else "NOT_AVAILABLE",
            "reason": reason_by_case[edge["case"]],
            "data_mode": edge["data_mode"],
            "watermark": WATERMARK,
        }
        for edge in edge_cases
    ]
    return {
        "schema_version": "ril-021-b0-v1",
        "fixture_id": fixture["fixture_id"],
        "source_fixture_sha256": fixture_checksum,
        "generated_at": "2026-01-15T00:00:00Z",
        "model": {
            "model_id": "B0_UNIFORM",
            "model_version": "b0-uniform-v1",
            "model_status": "ILLUSTRATIVE_NOT_VALIDATED",
            "method": "1/n over active eligible runners",
            "data_mode": "SYNTHETIC_ONLY",
        },
        "forecasts": forecasts,
        "edge_case_abstentions": abstentions,
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
        raise SystemExit(f"B0 MANIFEST CHECK FAILED: missing {args.output}")
    actual = load_json(args.output)
    if actual != expected:
        raise SystemExit("B0 MANIFEST CHECK FAILED: generated content differs")
    ready = sum(item["status"] == "READY" for item in expected["forecasts"])
    abstain = sum(item["status"] == "ABSTAIN" for item in expected["forecasts"])
    print(f"B0 MANIFEST VALID: forecasts={len(expected['forecasts'])} ready={ready} abstain={abstain} edge_abstentions={len(expected['edge_case_abstentions'])}")


if __name__ == "__main__":
    main()
