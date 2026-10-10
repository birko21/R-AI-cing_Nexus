from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.metrics import EvaluationRecord, evaluate_records  # noqa: E402


FIXTURE = ROOT / "fixtures" / "synthetic" / "fixture.json"
B1 = ROOT / "fixtures" / "synthetic" / "forecasts_b1.json"
OUTPUT = ROOT / "fixtures" / "synthetic" / "metrics_b1_v1.json"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report() -> dict[str, object]:
    fixture = load_json(FIXTURE)
    b1 = load_json(B1)
    collections = fixture["collections"]
    assert isinstance(collections, dict)
    races = {race["race_id"]: race for race in collections["races"]}
    results = {result["race_id"]: result for result in collections["results"]}
    records = []
    for forecast in b1["forecasts"]:
        race = races[forecast["race_id"]]
        result = results.get(forecast["race_id"])
        if race["status"] != "OFFICIAL" or result is None:
            continue
        probabilities = {runner["entry_id"]: runner["probability"] for runner in forecast["runners"]}
        records.append(EvaluationRecord(
            race_id=forecast["race_id"], code=forecast["code"],
            observed_at=datetime.fromisoformat(result["resolved_at"].replace("Z", "+00:00")),
            horizon="T+0", model_version=forecast["model_version"], probabilities=probabilities,
            winner_entry_id=result["winner_entry_id"], data_mode=forecast["data_mode"],
        ))
    report = evaluate_records(records, bootstrap_seed=20260115, bootstrap_repetitions=1000)
    report.update({"fixture_id": fixture["fixture_id"], "recorded_at": "2026-01-15T00:00:00Z"})
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_report()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("METRIC REPORT CHECK FAILED: generated content differs")
    print(f"METRIC REPORT VALID: n={expected['n']} codes={','.join(expected['codes'])}")


if __name__ == "__main__":
    main()
