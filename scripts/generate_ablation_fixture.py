"""Generate and validate the deterministic synthetic ablation report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.ablation import build_ablation_report, verify_ablation_report  # noqa: E402
from app.metrics import EvaluationRecord  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "ablation_v1.json"
UTC = timezone.utc
START = datetime(2026, 1, 1, tzinfo=UTC)
END = datetime(2026, 1, 5, tzinfo=UTC)


def records(model_version: str, values: tuple[tuple[float, float], ...]) -> tuple[EvaluationRecord, ...]:
    return tuple(
        EvaluationRecord(
            race_id=f"race-{index}", code="THOROUGHBRED", observed_at=datetime(2026, 1, index, tzinfo=UTC),
            horizon="T+0", model_version=model_version, probabilities={"a": first, "b": second},
            winner_entry_id="a" if index % 2 else "b", data_mode="SYNTHETIC_ONLY",
        )
        for index, (first, second) in enumerate(values, start=1)
    )


def build_fixture() -> dict[str, object]:
    report = build_ablation_report(
        records("B0_UNIFORM", ((0.5, 0.5), (0.5, 0.5), (0.5, 0.5), (0.5, 0.5))),
        records("TB_FORM_INCREMENTAL", ((0.6, 0.4), (0.4, 0.6), (0.55, 0.45), (0.45, 0.55))),
        study_id="synthetic-tb-form-ablation-v1", feature_family="FORM_ONLY", provider_id="synthetic-fixture",
        expected_race_ids=("race-1", "race-2", "race-3", "race-4"), holdout_start=START,
        holdout_end=END, bootstrap_seed=11, bootstrap_repetitions=100,
    )
    verify_ablation_report(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("ABLATION FIXTURE CHECK FAILED: generated content differs")
    print(f"ABLATION FIXTURE VALID: races={expected['coverage']['expected_races']} hash={expected['report_hash']}")


if __name__ == "__main__":
    main()
