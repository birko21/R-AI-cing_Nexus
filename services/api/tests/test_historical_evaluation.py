from datetime import datetime, timezone

import pytest

from app.historical_evaluation import ForecastCase, evaluate_forecasts


UTC = timezone.utc


def case(model: str, *, status: str = "SINGLE_WINNER", missing: tuple[str, ...] = (), fold_role: str = "TEST") -> ForecastCase:
    return ForecastCase(
        race_id=f"{model}-race", code="THOROUGHBRED", observed_at=datetime(2026, 1, 2, tzinfo=UTC), model_id=model, model_version="v1",
        probabilities={"a": 0.7, "b": 0.3}, winner_entry_id="a", outcome_status=status, track="Synthetic", distance=1200,
        race_type="WIN", feature_family=model, missingness=missing, market_probabilities={"a": 0.6, "b": 0.4}, fold_id="fold-001", fold_role=fold_role,
    )


def test_evaluation_reports_metrics_segments_ablation_market_comparison_and_walk_forward() -> None:
    report = evaluate_forecasts((case("B0"), case("B1", missing=("MISSING_SECTIONAL",))))

    assert report["status"] == "ILLUSTRATIVE_SYNTHETIC_ONLY"
    assert report["validated_claim"] is False
    assert report["scored_case_count"] == 2
    assert set(report["models"]) == {"B0", "B1"}
    assert report["walk_forward"]["status"] == "READY"
    assert report["market_comparison"]["B0"]["status"] == "ILLUSTRATIVE_SYNTHETIC_ONLY"
    assert report["missing_input_sensitivity"]["MISSING_INPUTS"]["n"] == 1


def test_evaluation_excludes_dead_heat_scratch_abandonment_coupled_and_non_test_cases() -> None:
    report = evaluate_forecasts((case("dead", status="DEAD_HEAT"), case("scratch", status="SCRATCHED"), case("train", fold_role="TRAIN")))

    assert report["status"] == "INSUFFICIENT_HISTORY"
    assert report["scored_case_count"] == 0
    assert {item["reason"] for item in report["excluded_cases"]} == {"DEAD_HEAT", "SCRATCHED", "NON_TEST_CASE"}


def test_evaluation_rejects_non_synthetic_until_rights_are_approved() -> None:
    real_case = case("real")
    real_case = ForecastCase(**{**real_case.__dict__, "data_mode": "LICENSED"})
    with pytest.raises(ValueError, match="synthetic-only"):
        evaluate_forecasts((real_case,))


def test_evaluation_allows_multiple_models_for_one_race_but_rejects_cross_fold_reuse() -> None:
    same_race = tuple(ForecastCase(**{**item.__dict__, "race_id": "shared-race"}) for item in (case("B0"), case("B1")))
    report = evaluate_forecasts(same_race)
    assert report["walk_forward"]["status"] == "READY"
    cross_fold = ForecastCase(**{**same_race[0].__dict__, "fold_id": "fold-002"})
    report = evaluate_forecasts((same_race[0], cross_fold))
    assert report["walk_forward"]["status"] == "INCOMPLETE"
    assert report["walk_forward"]["duplicate_fold_races"] is True
