from __future__ import annotations

import math

import pytest

from app.probability import (
    ProbabilityValidationError,
    categorical_log_loss,
    fair_decimal_odds,
    multiclass_brier_score,
    validate_probabilities,
)


def test_probability_validation_accepts_zero_and_tiny_normalization_error() -> None:
    validate_probabilities({"entry-1": 0.0, "entry-2": 0.9999999995, "entry-3": 0.0000000005}, ["entry-1", "entry-2", "entry-3"])


@pytest.mark.parametrize(
    "probabilities,field,match",
    [
        ({"entry-1": 0.5}, ["entry-1", "entry-2"], "membership mismatch"),
        ({"entry-1": -0.1, "entry-2": 1.1}, ["entry-1", "entry-2"], "non-negative"),
        ({"entry-1": math.nan, "entry-2": 1.0}, ["entry-1", "entry-2"], "finite"),
        ({"entry-1": math.inf, "entry-2": 0.0}, ["entry-1", "entry-2"], "finite"),
        ({"entry-1": 0.6, "entry-2": 0.3}, ["entry-1", "entry-2"], "outside tolerance"),
        ({"entry-1": 1.0, "entry-2": 0.0}, ["entry-1", "entry-1"], "duplicate"),
    ],
)
def test_probability_validation_rejects_invalid_distributions(probabilities: dict[str, float], field: list[str], match: str) -> None:
    with pytest.raises(ProbabilityValidationError, match=match):
        validate_probabilities(probabilities, field)


def test_probability_validation_has_absolute_sum_tolerance() -> None:
    with pytest.raises(ProbabilityValidationError):
        validate_probabilities({"entry-1": 0.5, "entry-2": 0.50000002}, ["entry-1", "entry-2"])


def test_fair_odds_is_zero_safe_and_rejects_out_of_range_values() -> None:
    assert fair_decimal_odds(0.0) is None
    assert fair_decimal_odds(0.25) == pytest.approx(4.0)
    assert fair_decimal_odds(1.0) == pytest.approx(1.0)
    with pytest.raises(ProbabilityValidationError):
        fair_decimal_odds(1.1)


def test_log_loss_and_brier_conventions_are_explicit() -> None:
    probabilities = {"entry-1": 0.25, "entry-2": 0.75}

    assert categorical_log_loss(probabilities, "entry-2") == pytest.approx(-math.log(0.75))
    assert multiclass_brier_score(probabilities, "entry-2") == pytest.approx(0.125)
    assert categorical_log_loss({"entry-1": 0.0, "entry-2": 1.0}, "entry-1") == math.inf
    with pytest.raises(ProbabilityValidationError, match="not a field entry"):
        categorical_log_loss(probabilities, "entry-3")

