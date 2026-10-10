from __future__ import annotations

from datetime import datetime, timezone
import math

import pytest

from app.metrics import EvaluationRecord, evaluate_records


UTC = timezone.utc


def record(race_id: str, code: str, day: int, probabilities: dict[str, float], winner: str, missingness: tuple[str, ...] = ()) -> EvaluationRecord:
    return EvaluationRecord(race_id, code, datetime(2026, 1, day, tzinfo=UTC), "T+0", "b0-uniform-v1", probabilities, winner, missingness)


def test_race_level_reference_log_loss_and_brier_are_reported() -> None:
    report = evaluate_records([
        record("race-1", "THOROUGHBRED", 1, {"a": 0.75, "b": 0.25}, "a"),
        record("race-2", "THOROUGHBRED", 2, {"a": 0.25, "b": 0.75}, "b"),
    ], bootstrap_seed=7, bootstrap_repetitions=100)

    assert report["n"] == 2
    assert report["log_loss"] == pytest.approx(-math.log(0.75))
    assert report["brier"] == pytest.approx(0.125)
    assert report["horizon"] == "T+0"
    assert report["model_version"] == "b0-uniform-v1"
    assert report["validated_claim"] is False
    assert report["metric_status"] == "IMPLEMENTATION_METRICS_SYNTHETIC_ONLY"


def test_report_contains_time_code_segments_calibration_missingness_and_ci() -> None:
    records = [
        record("tb-1", "THOROUGHBRED", 1, {"a": 0.6, "b": 0.4}, "a", ("MISSING_SECTIONAL",)),
        record("h-1", "HARNESS", 2, {"a": 0.5, "b": 0.5}, "b"),
    ]
    report = evaluate_records(records, bootstrap_seed=11, bootstrap_repetitions=50)

    assert report["codes"] == ["HARNESS", "THOROUGHBRED"]
    assert report["time_range"] == {"start": "2026-01-01T00:00:00Z", "end": "2026-01-02T00:00:00Z"}
    assert report["missingness"] == {"MISSING_SECTIONAL": 1}
    assert set(report["segments"]) == {"HARNESS", "THOROUGHBRED"}
    assert len(report["calibration"]) > 0
    assert len(report["confidence_intervals"]["log_loss_95"]) == 2


def test_bootstrap_confidence_intervals_are_seed_reproducible() -> None:
    records = [record("race-1", "GREYHOUND", 1, {"a": 0.8, "b": 0.2}, "a"), record("race-2", "GREYHOUND", 2, {"a": 0.4, "b": 0.6}, "b")]

    assert evaluate_records(records, bootstrap_seed=123, bootstrap_repetitions=30) == evaluate_records(records, bootstrap_seed=123, bootstrap_repetitions=30)


def test_metrics_reject_empty_naive_or_non_synthetic_inputs() -> None:
    with pytest.raises(ValueError, match="at least one"):
        evaluate_records([])
    with pytest.raises(ValueError, match="timezone-aware"):
        evaluate_records([EvaluationRecord("race", "HARNESS", datetime(2026, 1, 1), "T+0", "v1", {"a": 1.0}, "a")])
    with pytest.raises(ValueError, match="SYNTHETIC_ONLY"):
        evaluate_records([EvaluationRecord("race", "HARNESS", datetime(2026, 1, 1, tzinfo=UTC), "T+0", "v1", {"a": 1.0}, "a", data_mode="SCRAPED_PUBLIC")])
