from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from app.ablation import build_ablation_report, verify_ablation_report
from app.metrics import EvaluationRecord


UTC = timezone.utc
START = datetime(2026, 1, 1, tzinfo=UTC)
END = datetime(2026, 1, 4, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[3]


def records(model_version: str, winner: str = "a") -> tuple[EvaluationRecord, ...]:
    return tuple(
        EvaluationRecord(
            race_id=f"race-{index}", code="HARNESS", observed_at=datetime(2026, 1, index, tzinfo=UTC),
            horizon="T+0", model_version=model_version, probabilities={"a": 0.6, "b": 0.4},
            winner_entry_id=winner, data_mode="SYNTHETIC_ONLY",
        )
        for index in (1, 2, 3)
    )


def test_ablation_report_is_same_holdout_synthetic_only_and_hash_verified() -> None:
    report = build_ablation_report(
        records("B0_UNIFORM"), records("HARNESS_INCREMENTAL"), study_id="study-1", feature_family="FORM_ONLY",
        provider_id="synthetic-fixture", expected_race_ids=("race-1", "race-2", "race-3"),
        holdout_start=START, holdout_end=END, bootstrap_seed=7, bootstrap_repetitions=40,
    )

    verify_ablation_report(report)
    assert report["status"] == "IMPLEMENTATION_METRICS_SYNTHETIC_ONLY"
    assert report["validated_claim"] is False
    assert report["promotion"] == "HOLD"
    assert report["coverage"]["baseline_fraction"] == 1.0
    assert report["baseline"]["confidence_intervals"]["brier_95"]
    assert report == build_ablation_report(
        records("B0_UNIFORM"), records("HARNESS_INCREMENTAL"), study_id="study-1", feature_family="FORM_ONLY",
        provider_id="synthetic-fixture", expected_race_ids=("race-1", "race-2", "race-3"),
        holdout_start=START, holdout_end=END, bootstrap_seed=7, bootstrap_repetitions=40,
    )


def test_committed_ablation_fixture_is_valid_and_honest() -> None:
    report = json.loads((ROOT / "fixtures" / "synthetic" / "ablation_v1.json").read_text(encoding="utf-8"))
    verify_ablation_report(report)
    assert report["coverage"]["expected_races"] == 4
    assert report["data_mode"] == "SYNTHETIC_ONLY"
    assert report["promotion"] == "HOLD"


def test_ablation_rejects_different_races_or_future_holdout_records() -> None:
    with pytest.raises(ValueError, match="same races"):
        build_ablation_report(
            records("B0_UNIFORM"), records("HARNESS_INCREMENTAL")[:-1], study_id="study-1", feature_family="FORM_ONLY",
            provider_id="synthetic-fixture", expected_race_ids=("race-1", "race-2", "race-3"), holdout_start=START, holdout_end=END,
        )
    future = (EvaluationRecord(
        race_id="race-1", code="HARNESS", observed_at=datetime(2026, 1, 4, tzinfo=UTC), horizon="T+0",
        model_version="B0", probabilities={"a": 0.5, "b": 0.5}, winner_entry_id="a", data_mode="SYNTHETIC_ONLY",
    ),)
    with pytest.raises(ValueError, match="outside"):
        build_ablation_report(
            future, future, study_id="study-1", feature_family="FORM_ONLY", provider_id="synthetic-fixture",
            expected_race_ids=("race-1",), holdout_start=START, holdout_end=END,
        )
