from datetime import datetime, timezone, timedelta

import pytest

from app.model_benchmarks import (
    BenchmarkRace,
    BenchmarkRunner,
    MachineLearningBackendUnavailable,
    MarketInput,
    build_b0_forecast,
    build_b1_form_forecast,
    build_b2_market_forecast,
    build_b3_lightgbm_or_catboost,
    build_b4_market_informed_ensemble,
)


CUTOFF = datetime(2026, 1, 15, 1, tzinfo=timezone.utc)


def race() -> BenchmarkRace:
    return BenchmarkRace(
        "race-1", "THOROUGHBRED", CUTOFF,
        (BenchmarkRunner("a"), BenchmarkRunner("b")),
        {
            "a": {"historical_performance": 2.0, "recent_form": 2.0, "distance_suitability": 1.0, "adjusted_speed": 2.0, "class_fit": 1.0, "fitness": 1.0},
            "b": {"historical_performance": 1.0, "recent_form": 1.0, "distance_suitability": 1.0, "adjusted_speed": 1.0, "class_fit": 1.0, "fitness": 1.0},
        },
        {
            "a": MarketInput(2.0, 2.2, CUTOFF - timedelta(minutes=1), 20, 18, 100),
            "b": MarketInput(4.0, 4.2, CUTOFF - timedelta(minutes=1), 20, 18, 100),
        },
    )


def test_benchmarks_return_race_normalised_probabilities_and_keep_synthetic_status() -> None:
    forecasts = [build_b0_forecast(race()), build_b1_form_forecast(race()), build_b2_market_forecast(race()), build_b4_market_informed_ensemble(race())]
    assert all(forecast.state == "READY" for forecast in forecasts)
    assert all(sum(forecast.probabilities.values()) == pytest.approx(1.0) for forecast in forecasts)
    assert all(forecast.model_status == "ILLUSTRATIVE_NOT_VALIDATED" for forecast in forecasts)
    assert build_b2_market_forecast(race()).overround is not None
    assert build_b2_market_forecast(race()).spread_used is True


def test_market_baseline_rejects_future_prices_and_form_baseline_does_not_impute() -> None:
    future = race()
    future = BenchmarkRace(future.race_id, future.code, future.cutoff, future.runners, future.form_features, {"a": MarketInput(2.0, 2.1, CUTOFF + timedelta(minutes=1)), "b": future.market_inputs["b"]})
    assert build_b2_market_forecast(future).abstention_reason == "INCOMPLETE_MARKET"
    missing = BenchmarkRace(race().race_id, race().code, race().cutoff, race().runners, {"a": race().form_features["a"], "b": {}}, race().market_inputs)
    assert build_b1_form_forecast(missing).abstention_reason == "INSUFFICIENT_FORM_SUPPORT"


def test_benchmarks_abstain_on_coupled_entries_and_b3_is_explicitly_unavailable() -> None:
    coupled = BenchmarkRace(race().race_id, race().code, race().cutoff, (BenchmarkRunner("a", coupled_group="x"), BenchmarkRunner("b", coupled_group="x")), race().form_features, race().market_inputs)
    assert build_b0_forecast(coupled).state == "ABSTAIN"
    try:
        assert build_b3_lightgbm_or_catboost() is None
    except MachineLearningBackendUnavailable as exc:
        assert "NOT_AVAILABLE" in str(exc)
