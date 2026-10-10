"""Deterministic forecast explanations; no language model inference path."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math

from app.probability import fair_decimal_odds, validate_probabilities


@dataclass(frozen=True)
class EvidenceReference:
    source_provider: str
    dataset_reference: str
    source_receipt_id: str
    observation_timestamp: str | None
    limitation: str | None = None


@dataclass(frozen=True)
class FeatureContribution:
    entry_id: str
    feature_name: str
    value: float | None
    contribution: float
    evidence: tuple[EvidenceReference, ...]


@dataclass(frozen=True)
class ForecastExplanation:
    race_id: str
    code: str
    model_id: str
    model_version: str
    forecast_timestamp: str
    probabilities: dict[str, float]
    fair_decimal_odds: dict[str, float | None]
    material_contributions: tuple[FeatureContribution, ...]
    historical_evidence: tuple[EvidenceReference, ...]
    missing_or_unreliable_inputs: tuple[str, ...]
    uncertainty: dict[str, tuple[float, float]]
    calibration_status: str
    model_status: str
    model_differences: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "material_contributions": [
                {**asdict(item), "evidence": [asdict(reference) for reference in item.evidence]}
                for item in self.material_contributions
            ],
            "historical_evidence": [asdict(reference) for reference in self.historical_evidence],
        }


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("forecast timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_forecast_explanation(
    *, race_id: str, code: str, model_id: str, model_version: str, forecast_timestamp: datetime,
    probabilities: dict[str, float], contributions: tuple[FeatureContribution, ...], evidence: tuple[EvidenceReference, ...],
    missing_or_unreliable_inputs: tuple[str, ...], uncertainty: dict[str, tuple[float, float]], calibration_status: str,
    model_status: str, form_probabilities: dict[str, float] | None = None, market_probabilities: dict[str, float] | None = None,
) -> ForecastExplanation:
    """Build an auditable explanation from already verified model outputs."""

    validate_probabilities(probabilities, probabilities.keys())
    if any("starting_price" in contribution.feature_name.lower() for contribution in contributions):
        raise ValueError("post-race starting price cannot be a pre-race explanation feature")
    for entry_id, interval in uncertainty.items():
        if entry_id not in probabilities or len(interval) != 2 or not all(math.isfinite(value) for value in interval) or interval[0] < 0 or interval[1] > 1 or interval[0] > interval[1]:
            raise ValueError("uncertainty interval is invalid")
    differences: dict[str, float] = {}
    if form_probabilities is not None and market_probabilities is not None:
        validate_probabilities(form_probabilities, probabilities.keys())
        validate_probabilities(market_probabilities, probabilities.keys())
        differences = {entry_id: form_probabilities[entry_id] - market_probabilities[entry_id] for entry_id in probabilities}
    material = tuple(sorted(contributions, key=lambda item: (-abs(item.contribution), item.entry_id, item.feature_name)))
    return ForecastExplanation(
        race_id=race_id, code=code, model_id=model_id, model_version=model_version,
        forecast_timestamp=_timestamp(forecast_timestamp), probabilities=dict(probabilities),
        fair_decimal_odds={entry_id: fair_decimal_odds(probability) for entry_id, probability in probabilities.items()},
        material_contributions=material, historical_evidence=evidence,
        missing_or_unreliable_inputs=tuple(sorted(set(missing_or_unreliable_inputs))), uncertainty=uncertainty,
        calibration_status=calibration_status, model_status=model_status, model_differences=differences,
    )
