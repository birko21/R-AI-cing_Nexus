from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.diagnostics import diagnose_forecast  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "diagnostics_v1.json"


def build_fixture() -> dict[str, object]:
    scenarios = [
        {"scenario": "SUPPORTED_CLEAN", "probabilities": {"entry-1": 0.7, "entry-2": 0.3}, "support_count": 4, "comparison_probabilities": {"entry-1": 0.72, "entry-2": 0.28}},
        {"scenario": "MISSING_SPECIALTY_INPUT", "probabilities": {"entry-1": 0.6, "entry-2": 0.4}, "support_count": 3, "missingness": ["MISSING_SECTIONAL"]},
        {"scenario": "OOD_AND_DISAGREEMENT", "probabilities": {"entry-1": 0.6, "entry-2": 0.4}, "support_count": 3, "comparison_probabilities": {"entry-1": 0.95, "entry-2": 0.05}, "ood_score": 0.9},
    ]
    records = []
    for scenario in scenarios:
        inputs = {key: value for key, value in scenario.items() if key != "scenario"}
        result = diagnose_forecast(**inputs)
        records.append({"scenario": scenario["scenario"], "data_mode": "SYNTHETIC_ONLY", "diagnostics": result.to_dict()})
    return {"schema_version": "diagnostics-v1", "records": records, "fictional": True, "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("DIAGNOSTICS FIXTURE CHECK FAILED: generated content differs")
    print(f"DIAGNOSTICS FIXTURE VALID: records={len(expected['records'])}")


if __name__ == "__main__":
    main()
