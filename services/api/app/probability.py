"""Probability validation and race-level scoring conventions."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping


NORMALIZATION_TOLERANCE = 1e-8


class ProbabilityValidationError(ValueError):
    """Raised when a forecast cannot be treated as a normalized race distribution."""


def validate_probabilities(
    probabilities: Mapping[str, float],
    field_entry_ids: Iterable[str],
    *,
    tolerance: float = NORMALIZATION_TOLERANCE,
) -> None:
    """Validate one probability for every and only every field entry."""

    field_ids = tuple(field_entry_ids)
    if len(set(field_ids)) != len(field_ids):
        raise ProbabilityValidationError("field membership contains duplicate entry IDs")
    if set(probabilities) != set(field_ids):
        missing = sorted(set(field_ids) - set(probabilities))
        extra = sorted(set(probabilities) - set(field_ids))
        raise ProbabilityValidationError(f"field membership mismatch: missing={missing} extra={extra}")
    if tolerance < 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and non-negative")
    values = tuple(probabilities.values())
    for entry_id, probability in probabilities.items():
        if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not math.isfinite(probability):
            raise ProbabilityValidationError(f"probability for {entry_id} must be finite")
        if probability < 0:
            raise ProbabilityValidationError(f"probability for {entry_id} must be non-negative")
    total = math.fsum(values)
    if abs(total - 1.0) > tolerance:
        raise ProbabilityValidationError(f"probabilities sum to {total}, outside tolerance {tolerance}")


def fair_decimal_odds(probability: float) -> float | None:
    """Return decimal fair odds, or None when p=0 has no finite fair odds."""

    if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not math.isfinite(probability):
        raise ProbabilityValidationError("probability must be finite")
    if probability < 0 or probability > 1:
        raise ProbabilityValidationError("probability must be between 0 and 1")
    if probability == 0:
        return None
    return 1.0 / probability


def categorical_log_loss(probabilities: Mapping[str, float], winner_entry_id: str) -> float:
    """Use natural-log loss; a zero-probability observed winner scores infinity."""

    validate_probabilities(probabilities, probabilities.keys())
    if winner_entry_id not in probabilities:
        raise ProbabilityValidationError("winner is not a field entry")
    probability = probabilities[winner_entry_id]
    return math.inf if probability == 0 else -math.log(probability)


def multiclass_brier_score(probabilities: Mapping[str, float], winner_entry_id: str) -> float:
    """Return the multiclass Brier score: sum((p_i - y_i)^2)."""

    validate_probabilities(probabilities, probabilities.keys())
    if winner_entry_id not in probabilities:
        raise ProbabilityValidationError("winner is not a field entry")
    return math.fsum((probability - (1.0 if entry_id == winner_entry_id else 0.0)) ** 2 for entry_id, probability in probabilities.items())

