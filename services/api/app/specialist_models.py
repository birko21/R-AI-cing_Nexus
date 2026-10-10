"""Independent code-specialist model input contracts.

This module prepares leakage-safe, race-normalised inputs for later fitting. It
does not fit, promote or claim a predictive model. Every returned manifest is
explicitly illustrative until a walk-forward evaluation and independent
assurance record exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Literal


RacingCode = Literal["THOROUGHBRED", "HARNESS", "GREYHOUND"]
ModelFamily = Literal["FORM_ONLY", "MARKET_ONLY", "COMBINED"]
MODEL_STATUS = "ILLUSTRATIVE_NOT_VALIDATED"


FORM_FEATURES: dict[RacingCode, frozenset[str]] = {
    "THOROUGHBRED": frozenset({
        "historical_performance", "recent_form", "performance_trend", "distance_suitability", "track_suitability",
        "raw_speed", "adjusted_speed", "sectional_time", "finishing_speed", "race_class", "field_strength",
        "barrier", "track_condition", "venue_characteristics", "jockey_effect", "trainer_effect", "fitness",
        "rest_days", "recent_activity", "race_pace", "early_speed", "expected_position", "runner_interaction",
    }),
    "HARNESS": frozenset({
        "historical_performance", "recent_form", "performance_trend", "distance_suitability", "track_suitability",
        "raw_speed", "adjusted_speed", "sectional_time", "finishing_speed", "race_class", "field_strength",
        "barrier", "track_condition", "venue_characteristics", "driver_effect", "trainer_effect", "fitness",
        "rest_days", "recent_activity", "race_pace", "early_speed", "expected_position", "runner_interaction",
    }),
    "GREYHOUND": frozenset({
        "historical_performance", "recent_form", "performance_trend", "distance_suitability", "track_suitability",
        "raw_speed", "adjusted_speed", "sectional_time", "finishing_speed", "race_class", "field_strength",
        "box", "track_condition", "venue_characteristics", "trainer_effect", "fitness", "rest_days",
        "recent_activity", "race_pace", "early_speed", "expected_position", "runner_interaction",
    }),
}
MARKET_FEATURES = frozenset({
    "pre_race_price", "price_movement", "price_spread", "available_back_volume", "available_lay_volume",
    "matched_volume", "market_depth", "market_state",
})

# Starting price is retained as an explicitly separate post-race diagnostic;
# it is not a default pre-race feature and therefore cannot leak into training.
POST_RACE_DIAGNOSTICS = frozenset({"starting_price_diagnostic"})


@dataclass(frozen=True)
class FeatureObservation:
    participant_id: str
    feature_name: str
    value: float | None
    observed_at: datetime
    retrieved_at: datetime
    source_receipt_id: str
    rights_state: str


@dataclass(frozen=True)
class SpecialistInputSnapshot:
    code: RacingCode
    family: ModelFamily
    race_id: str
    cutoff: str
    model_status: str
    values: dict[str, dict[str, float | None]]
    included_receipt_ids: tuple[str, ...]
    excluded_future_receipt_ids: tuple[str, ...]
    excluded_unapproved_receipt_ids: tuple[str, ...]
    missing_reasons: dict[str, dict[str, str]]


def model_feature_set(code: RacingCode, family: ModelFamily) -> frozenset[str]:
    if code not in FORM_FEATURES:
        raise ValueError(f"unsupported specialist racing code: {code}")
    if family == "FORM_ONLY":
        return FORM_FEATURES[code]
    if family == "MARKET_ONLY":
        return MARKET_FEATURES
    if family == "COMBINED":
        return FORM_FEATURES[code] | MARKET_FEATURES
    raise ValueError(f"unsupported specialist model family: {family}")


def specialist_model_manifest(code: RacingCode, family: ModelFamily) -> dict[str, object]:
    """Describe one independent model target without asserting it is fitted."""

    return {
        "model_id": f"{code.lower()}-{family.lower()}",
        "code": code,
        "family": family,
        "feature_names": sorted(model_feature_set(code, family)),
        "model_status": MODEL_STATUS,
        "validation_required": ["walk_forward", "race_normalisation", "calibration", "independent_assurance"],
    }


def _cutoff_text(cutoff: datetime) -> str:
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("specialist model cutoff must be timezone-aware")
    return cutoff.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalise(values: list[float]) -> dict[int, float]:
    if not values:
        return {}
    mean = math.fsum(values) / len(values)
    variance = math.fsum((value - mean) ** 2 for value in values) / len(values)
    deviation = math.sqrt(variance)
    return {index: (value - mean) / deviation if deviation else 0.0 for index, value in enumerate(values)}


def materialize_specialist_inputs(
    *, code: RacingCode, family: ModelFamily, race_id: str, cutoff: datetime,
    participant_ids: tuple[str, ...], observations: tuple[FeatureObservation, ...],
) -> SpecialistInputSnapshot:
    """Build race-normalised, pre-cutoff inputs and preserve every exclusion reason."""

    cutoff_text = _cutoff_text(cutoff)
    if len(set(participant_ids)) != len(participant_ids):
        raise ValueError("specialist field contains duplicate participant IDs")
    if not participant_ids:
        raise ValueError("specialist field cannot be empty")
    allowed = model_feature_set(code, family)
    values = {participant_id: {} for participant_id in participant_ids}
    missing = {participant_id: {} for participant_id in participant_ids}
    included: list[str] = []
    future: list[str] = []
    unapproved: list[str] = []
    usable: dict[tuple[str, str], FeatureObservation] = {}
    for observation in observations:
        if observation.participant_id not in values or observation.feature_name not in allowed:
            continue
        if observation.observed_at.tzinfo is None or observation.retrieved_at.tzinfo is None:
            raise ValueError("specialist observations require timezone-aware timestamps")
        if observation.observed_at >= cutoff or observation.retrieved_at > cutoff:
            future.append(observation.source_receipt_id)
            continue
        if observation.rights_state not in {"SYNTHETIC", "APPROVED"}:
            unapproved.append(observation.source_receipt_id)
            continue
        key = (observation.participant_id, observation.feature_name)
        if key in usable:
            raise ValueError("duplicate specialist feature observation")
        usable[key] = observation
        included.append(observation.source_receipt_id)

    for participant_id in participant_ids:
        for feature_name in sorted(allowed):
            observation = usable.get((participant_id, feature_name))
            if observation is None:
                values[participant_id][feature_name] = None
                missing[participant_id][feature_name] = "NO_APPROVED_PRE_CUTOFF_OBSERVATION"
            elif observation.value is None or not math.isfinite(observation.value):
                values[participant_id][feature_name] = None
                missing[participant_id][feature_name] = "NONFINITE_OR_MISSING_VALUE"
            else:
                values[participant_id][feature_name] = observation.value

    for feature_name in sorted(allowed):
        present = [(participant_id, values[participant_id][feature_name]) for participant_id in participant_ids if values[participant_id][feature_name] is not None]
        normalised = _normalise([value for _, value in present if value is not None])
        for index, (participant_id, _) in enumerate(present):
            values[participant_id][feature_name] = normalised[index]

    return SpecialistInputSnapshot(
        code=code, family=family, race_id=race_id, cutoff=cutoff_text, model_status=MODEL_STATUS,
        values=values, included_receipt_ids=tuple(sorted(set(included))),
        excluded_future_receipt_ids=tuple(sorted(set(future))),
        excluded_unapproved_receipt_ids=tuple(sorted(set(unapproved))), missing_reasons=missing,
    )
