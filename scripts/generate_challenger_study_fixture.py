from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.challenger_study import ModelScore, StudySpec, compare_challenger  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "challenger_study_v1.json"
START = datetime(2025, 12, 1, tzinfo=timezone.utc)
END = datetime(2026, 1, 1, tzinfo=timezone.utc)


def build_fixture() -> dict[str, object]:
    spec = StudySpec(study_id="study-1", preregistered_at=datetime(2025, 11, 1, tzinfo=timezone.utc), holdout_start=START, holdout_end=END, challenger_id="TB_CHALLENGER_V1", metric="BRIER", data_mode="SYNTHETIC_ONLY")
    values = {"B0_UNIFORM": 0.30, "B1_FORM_HEURISTIC": 0.28, "MARKET_BASELINE": 0.25, "TB_CHALLENGER_V1": 0.20}
    scores = tuple(ModelScore(model_id=model_id, holdout_start=START, holdout_end=END, sample_size=100, metric_value=value, ci_low=value - 0.02, ci_high=value + 0.02) for model_id, value in values.items())
    report = compare_challenger(spec, scores)
    return {
        "schema_version": "challenger-study-v1", "preregistered_spec": spec.model_dump(mode="json"), "report": report.model_dump(mode="json"),
        "fictional": True, "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Synthetic chronological holdout evidence only; promotion remains HOLD without independent assurance and owner approval.",
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
        raise SystemExit("CHALLENGER STUDY FIXTURE CHECK FAILED: generated content differs")
    print(f"CHALLENGER STUDY FIXTURE VALID: models={len(expected['report']['scores'])} promotion={expected['report']['promotion']['status']}")


if __name__ == "__main__":
    main()
