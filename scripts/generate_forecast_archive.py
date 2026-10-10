from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.forecast_archive import create_forecast_manifest, verify_manifest  # noqa: E402


WATERMARK = "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE"
OUTPUT = ROOT / "fixtures" / "synthetic" / "forecast_archive.json"
B1_MANIFEST = ROOT / "fixtures" / "synthetic" / "forecasts_b1.json"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_archive() -> dict[str, object]:
    b1 = load_json(B1_MANIFEST)
    forecasts = b1["forecasts"]
    assert isinstance(forecasts, list)
    records: list[dict[str, object]] = []
    for forecast in forecasts:
        runners = forecast["runners"]
        assert isinstance(runners, list)
        feature_snapshot = {
            "target_distance": forecast["target_distance"],
            "runners": {runner["entry_id"]: runner["features"] for runner in runners},
        }
        model_descriptor = {
            "model_id": forecast["model_id"],
            "model_version": forecast["model_version"],
            "weights": forecast["weights"],
            "smoothing": forecast["smoothing"],
            "minimum_support": forecast["minimum_support"],
        }
        output = {"probabilities": {runner["entry_id"]: runner["probability"] for runner in runners}}
        manifest = create_forecast_manifest(
            forecast_id=forecast["forecast_id"], race_id=forecast["race_id"], field_revision=forecast["field_revision"],
            cutoff=forecast["cutoff"], feature_snapshot=feature_snapshot, model_descriptor=model_descriptor,
            active_runner_ids=[runner["entry_id"] for runner in runners], data_mode=forecast["data_mode"],
            diagnostic_flags=forecast["diagnostics"], output=output,
        ).to_dict()
        verify_manifest(manifest)
        records.append(manifest)
    return {
        "schema_version": "ril-024-forecast-archive-v1",
        "fixture_id": b1["fixture_id"],
        "source_b1_manifest_sha256": b1["source_fixture_sha256"],
        "model_status": "ILLUSTRATIVE_NOT_VALIDATED",
        "invalidation_policy": {
            "SCRATCHING": "INVALIDATE_PRIOR_CREATE_NEW_REVISION",
            "RESERVE": "INVALIDATE_PRIOR_CREATE_NEW_REVISION",
            "CORRECTION": "INVALIDATE_PRIOR_CREATE_NEW_REVISION",
            "COUPLED_ENTRY": "ABSTAIN",
            "DEAD_HEAT": "ABSTAIN_OR_EXCLUDE_PRIMARY_SCORING",
        },
        "records": records,
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
    expected = build_archive()
    if args.write:
        write_json(args.output, expected)
    if not args.output.exists():
        raise SystemExit(f"FORECAST ARCHIVE CHECK FAILED: missing {args.output}")
    if load_json(args.output) != expected:
        raise SystemExit("FORECAST ARCHIVE CHECK FAILED: generated content differs")
    print(f"FORECAST ARCHIVE VALID: records={len(expected['records'])}")


if __name__ == "__main__":
    main()
