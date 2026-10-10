from datetime import datetime, timezone

import pytest

from app.explainability import EvidenceReference, FeatureContribution, build_forecast_explanation


def test_explanation_contains_fair_odds_evidence_uncertainty_and_model_difference() -> None:
    evidence = EvidenceReference("synthetic", "runs-v1", "receipt-1", "2026-01-15T00:00:00Z")
    result = build_forecast_explanation(
        race_id="race-1", code="THOROUGHBRED", model_id="B4", model_version="v1", forecast_timestamp=datetime(2026, 1, 15, 1, tzinfo=timezone.utc),
        probabilities={"a": 0.75, "b": 0.25},
        contributions=(FeatureContribution("a", "adjusted_speed", 1.2, 0.2, (evidence,)), FeatureContribution("b", "recent_form", 0.2, -0.1, ())),
        evidence=(evidence,), missing_or_unreliable_inputs=("MISSING_SECTIONAL",), uncertainty={"a": (0.65, 0.82), "b": (0.18, 0.35)},
        calibration_status="NOT_CALIBRATED", model_status="ILLUSTRATIVE_NOT_VALIDATED", form_probabilities={"a": 0.8, "b": 0.2}, market_probabilities={"a": 0.7, "b": 0.3},
    )
    assert result.fair_decimal_odds["a"] == pytest.approx(4 / 3)
    assert result.material_contributions[0].feature_name == "adjusted_speed"
    assert result.model_differences == {"a": pytest.approx(0.1), "b": pytest.approx(-0.1)}
    assert result.missing_or_unreliable_inputs == ("MISSING_SECTIONAL",)


def test_explanation_rejects_postrace_starting_price_and_invalid_uncertainty() -> None:
    with pytest.raises(ValueError, match="starting price"):
        build_forecast_explanation(
            race_id="r", code="GREYHOUND", model_id="B2", model_version="v1", forecast_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            probabilities={"a": 1.0}, contributions=(FeatureContribution("a", "starting_price_diagnostic", 2.0, 1.0, ()),), evidence=(),
            missing_or_unreliable_inputs=(), uncertainty={"a": (0.0, 1.0)}, calibration_status="NOT_CALIBRATED", model_status="ILLUSTRATIVE_NOT_VALIDATED",
        )
    with pytest.raises(ValueError, match="uncertainty"):
        build_forecast_explanation(
            race_id="r", code="GREYHOUND", model_id="B2", model_version="v1", forecast_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            probabilities={"a": 1.0}, contributions=(), evidence=(), missing_or_unreliable_inputs=(), uncertainty={"a": (0.8, 0.2)}, calibration_status="NOT_CALIBRATED", model_status="ILLUSTRATIVE_NOT_VALIDATED",
        )
