"""Rights-aware, leakage-safe historical feature generation for all codes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from collections import defaultdict
from typing import Literal


RacingCode = Literal["THOROUGHBRED", "HARNESS", "GREYHOUND"]
FeatureTransform = Literal["IDENTITY", "LOG1P", "NEGATE"]
Normalisation = Literal["NONE", "RACE_ZSCORE"]
RightsState = Literal["SYNTHETIC", "APPROVED", "UNASSESSED", "RESTRICTED", "REJECTED"]
QualityState = Literal["VALID", "MISSING", "INVALID", "CONFLICT", "DUPLICATE"]

FEATURE_GENERATION_VERSION = "historical-features-v1"
SUPPORTED_CODES = frozenset({"THOROUGHBRED", "HARNESS", "GREYHOUND"})
USABLE_RIGHTS = frozenset({"SYNTHETIC", "APPROVED"})


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    unit: str
    transform: FeatureTransform = "IDENTITY"
    normalisation: Normalisation = "RACE_ZSCORE"
    critical: bool = False


@dataclass(frozen=True)
class FeatureObservation:
    provider_id: str
    dataset_reference: str
    code: RacingCode
    race_id: str
    participant_id: str
    provider_participant_id: str
    feature_name: str
    value: float | None
    unit: str
    observed_at: datetime
    published_at: datetime | None
    retrieved_at: datetime
    pre_race_eligible_at: datetime
    source_receipt_id: str
    rights_state: RightsState
    retention_class: str
    quality_state: QualityState = "VALID"
    identity_link_id: str | None = None
    identity_evidence: Literal["EXACT", "RECONCILED", "NAME_ONLY"] = "NAME_ONLY"

    def __post_init__(self) -> None:
        if self.code not in SUPPORTED_CODES:
            raise ValueError(f"unsupported feature code: {self.code}")
        for name, value in (
            ("observed_at", self.observed_at), ("retrieved_at", self.retrieved_at),
            ("pre_race_eligible_at", self.pre_race_eligible_at),
        ):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.published_at is not None and (self.published_at.tzinfo is None or self.published_at.utcoffset() is None):
            raise ValueError("published_at must be timezone-aware")
        if self.published_at is not None and self.published_at > self.retrieved_at:
            raise ValueError("published_at cannot be later than retrieved_at")
        if self.value is not None and not math.isfinite(self.value):
            raise ValueError("feature value must be finite or null")
        if self.identity_link_id is not None and self.identity_evidence == "NAME_ONLY":
            raise ValueError("identity link requires exact or reconciled evidence")


@dataclass(frozen=True)
class FeatureRecord:
    generation_version: str
    source_provider: str
    dataset_reference: str
    race_id: str
    participant_id: str
    provider_participant_id: str
    feature_name: str
    unit: str
    transform: FeatureTransform
    normalisation: Normalisation
    value: float | None
    observed_at: str | None
    published_at: str | None
    pre_race_eligible_at: str | None
    source_receipt_id: str | None
    quality_state: QualityState
    missing_reason: str | None
    rights_state: RightsState
    retention_class: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FeatureExclusion:
    source_receipt_id: str
    reason: str
    provider_id: str
    participant_id: str
    feature_name: str


@dataclass(frozen=True)
class FeatureSnapshot:
    schema_version: str
    race_id: str
    code: RacingCode
    cutoff: str
    records: dict[str, dict[str, FeatureRecord]]
    exclusions: tuple[FeatureExclusion, ...]
    critical_missing: tuple[str, ...]
    snapshot_hash: str

    def to_dict(self) -> dict[str, object]:
        payload = {
            "schema_version": self.schema_version,
            "race_id": self.race_id,
            "code": self.code,
            "cutoff": self.cutoff,
            "records": {participant: {name: record.to_dict() for name, record in values.items()} for participant, values in self.records.items()},
            "exclusions": [asdict(item) for item in self.exclusions],
            "critical_missing": list(self.critical_missing),
        }
        return {**payload, "snapshot_hash": self.snapshot_hash}


def _timestamp(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _cutoff(value: datetime) -> tuple[datetime, str]:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("feature cutoff must be timezone-aware")
    normalized = value.astimezone(timezone.utc)
    return normalized, _timestamp(normalized) or ""


def _transform(value: float, name: FeatureTransform) -> float:
    if name == "IDENTITY":
        return value
    if name == "LOG1P":
        if value < 0:
            raise ValueError("LOG1P feature values must be non-negative")
        return math.log1p(value)
    if name == "NEGATE":
        return -value
    raise ValueError(f"unsupported feature transform: {name}")


def _zscore(values: list[float]) -> dict[int, float]:
    if not values:
        return {}
    mean = math.fsum(values) / len(values)
    variance = math.fsum((value - mean) ** 2 for value in values) / len(values)
    sd = math.sqrt(variance)
    return {index: ((value - mean) / sd if sd else 0.0) for index, value in enumerate(values)}


def default_feature_definitions(code: RacingCode) -> dict[str, FeatureDefinition]:
    if code not in SUPPORTED_CODES:
        raise ValueError(f"unsupported feature code: {code}")
    common = {
        "historical_performance": FeatureDefinition("historical_performance", "score", critical=True),
        "recent_form": FeatureDefinition("recent_form", "score"),
        "performance_trend": FeatureDefinition("performance_trend", "score"),
        "distance_suitability": FeatureDefinition("distance_suitability", "ratio"),
        "track_suitability": FeatureDefinition("track_suitability", "ratio"),
        "raw_speed": FeatureDefinition("raw_speed", "m/s"),
        "adjusted_speed": FeatureDefinition("adjusted_speed", "score"),
        "sectional_time": FeatureDefinition("sectional_time", "seconds", "NEGATE"),
        "finishing_speed": FeatureDefinition("finishing_speed", "m/s"),
        "race_class": FeatureDefinition("race_class", "score"),
        "field_strength": FeatureDefinition("field_strength", "score"),
        "track_condition": FeatureDefinition("track_condition", "score"),
        "venue_characteristics": FeatureDefinition("venue_characteristics", "score"),
        "trainer_effect": FeatureDefinition("trainer_effect", "score"),
        "fitness": FeatureDefinition("fitness", "score"),
        "rest_days": FeatureDefinition("rest_days", "days", "LOG1P"),
        "recent_activity": FeatureDefinition("recent_activity", "count", "LOG1P"),
        "race_pace": FeatureDefinition("race_pace", "score"),
        "early_speed": FeatureDefinition("early_speed", "m/s"),
        "expected_position": FeatureDefinition("expected_position", "position", "NEGATE"),
        "runner_interaction": FeatureDefinition("runner_interaction", "score"),
        "pre_race_price": FeatureDefinition("pre_race_price", "decimal_odds", "NEGATE"),
        "price_movement": FeatureDefinition("price_movement", "decimal_odds"),
        "price_spread": FeatureDefinition("price_spread", "decimal_odds", "NEGATE"),
        "available_back_volume": FeatureDefinition("available_back_volume", "currency", "LOG1P"),
        "available_lay_volume": FeatureDefinition("available_lay_volume", "currency", "LOG1P"),
        "matched_volume": FeatureDefinition("matched_volume", "currency", "LOG1P"),
        "market_depth": FeatureDefinition("market_depth", "count", "LOG1P"),
        "market_state": FeatureDefinition("market_state", "score"),
    }
    if code == "THOROUGHBRED":
        common.update({"barrier": FeatureDefinition("barrier", "number", "NEGATE"), "jockey_effect": FeatureDefinition("jockey_effect", "score")})
    elif code == "HARNESS":
        common.update({"barrier": FeatureDefinition("barrier", "number", "NEGATE"), "driver_effect": FeatureDefinition("driver_effect", "score")})
    else:
        common.update({"box": FeatureDefinition("box", "number", "NEGATE")})
    return common


def _record_from_observation(observation: FeatureObservation, definition: FeatureDefinition, *, value: float | None, quality: QualityState, missing_reason: str | None) -> FeatureRecord:
    return FeatureRecord(
        generation_version=FEATURE_GENERATION_VERSION, source_provider=observation.provider_id,
        dataset_reference=observation.dataset_reference, race_id=observation.race_id,
        participant_id=observation.participant_id, provider_participant_id=observation.provider_participant_id,
        feature_name=observation.feature_name, unit=definition.unit, transform=definition.transform,
        normalisation=definition.normalisation, value=value, observed_at=_timestamp(observation.observed_at),
        published_at=_timestamp(observation.published_at), pre_race_eligible_at=_timestamp(observation.pre_race_eligible_at),
        source_receipt_id=observation.source_receipt_id, quality_state=quality, missing_reason=missing_reason,
        rights_state=observation.rights_state, retention_class=observation.retention_class,
    )


def generate_feature_snapshot(
    *, race_id: str, code: RacingCode, cutoff: datetime, participant_ids: tuple[str, ...],
    observations: tuple[FeatureObservation, ...], definitions: dict[str, FeatureDefinition] | None = None,
) -> FeatureSnapshot:
    """Generate one race snapshot without imputation or unsafe provider joins."""

    cutoff_value, cutoff_text = _cutoff(cutoff)
    if not participant_ids or len(set(participant_ids)) != len(participant_ids):
        raise ValueError("feature field participant IDs must be non-empty and unique")
    definitions = definitions or default_feature_definitions(code)
    records: dict[str, dict[str, FeatureRecord]] = {participant: {} for participant in participant_ids}
    exclusions: list[FeatureExclusion] = []

    for observation in observations:
        if observation.race_id != race_id or observation.code != code:
            exclusions.append(FeatureExclusion(observation.source_receipt_id, "RACE_OR_CODE_MISMATCH", observation.provider_id, observation.participant_id, observation.feature_name))
            continue
        if observation.participant_id not in records:
            exclusions.append(FeatureExclusion(observation.source_receipt_id, "RUNNER_NOT_IN_FIELD", observation.provider_id, observation.participant_id, observation.feature_name))
            continue
        if observation.feature_name not in definitions:
            exclusions.append(FeatureExclusion(observation.source_receipt_id, "FEATURE_NOT_DECLARED", observation.provider_id, observation.participant_id, observation.feature_name))
            continue

    by_participant_providers: dict[str, set[str]] = defaultdict(set)
    for observation in observations:
        if observation.race_id == race_id and observation.code == code and observation.participant_id in records:
            by_participant_providers[observation.participant_id].add(observation.provider_id)
    unsafe_join_participants = {
        participant for participant, providers in by_participant_providers.items() if len(providers) > 1
        and any(observation.participant_id == participant and observation.identity_evidence not in {"EXACT", "RECONCILED"} for observation in observations)
    }

    candidates: dict[tuple[str, str, str, str], list[FeatureObservation]] = defaultdict(list)
    for observation in observations:
        if observation.race_id != race_id or observation.code != code or observation.participant_id not in records or observation.feature_name not in definitions:
            continue
        if observation.rights_state not in USABLE_RIGHTS:
            exclusions.append(FeatureExclusion(observation.source_receipt_id, "RIGHTS_NOT_APPROVED", observation.provider_id, observation.participant_id, observation.feature_name))
            continue
        if observation.pre_race_eligible_at >= cutoff_value or observation.observed_at >= cutoff_value or observation.retrieved_at > cutoff_value or (observation.published_at is not None and observation.published_at > cutoff_value):
            exclusions.append(FeatureExclusion(observation.source_receipt_id, "POST_CUTOFF_OR_UNVERIFIED", observation.provider_id, observation.participant_id, observation.feature_name))
            continue
        if observation.quality_state != "VALID":
            exclusions.append(FeatureExclusion(observation.source_receipt_id, f"QUALITY_{observation.quality_state}", observation.provider_id, observation.participant_id, observation.feature_name))
            continue
        definition = definitions[observation.feature_name]
        if observation.unit != definition.unit:
            exclusions.append(FeatureExclusion(observation.source_receipt_id, "UNIT_MISMATCH", observation.provider_id, observation.participant_id, observation.feature_name))
            continue
        if observation.participant_id in unsafe_join_participants:
            exclusions.append(FeatureExclusion(observation.source_receipt_id, "IDENTITY_LINK_REQUIRED", observation.provider_id, observation.participant_id, observation.feature_name))
            continue
        candidates[(observation.participant_id, observation.provider_id, observation.dataset_reference, observation.feature_name)].append(observation)

    selected: dict[tuple[str, str], FeatureRecord] = {}
    for key, values in candidates.items():
        values = sorted(values, key=lambda item: (item.pre_race_eligible_at, item.retrieved_at, item.source_receipt_id))
        latest = values[-1]
        if len(values) > 1 and values[-1].pre_race_eligible_at == values[-2].pre_race_eligible_at:
            exclusions.extend(FeatureExclusion(item.source_receipt_id, "DUPLICATE_ELIGIBILITY_TIMESTAMP", item.provider_id, item.participant_id, item.feature_name) for item in values)
            continue
        definition = definitions[latest.feature_name]
        if latest.value is None:
            selected[(latest.participant_id, f"{latest.provider_id}:{latest.dataset_reference}:{latest.feature_name}")] = _record_from_observation(latest, definition, value=None, quality="MISSING", missing_reason="SOURCE_VALUE_MISSING")
        else:
            try:
                value = _transform(latest.value, definition.transform)
            except ValueError:
                exclusions.append(FeatureExclusion(latest.source_receipt_id, "TRANSFORM_INVALID", latest.provider_id, latest.participant_id, latest.feature_name))
                continue
            selected[(latest.participant_id, f"{latest.provider_id}:{latest.dataset_reference}:{latest.feature_name}")] = _record_from_observation(latest, definition, value=value, quality="VALID", missing_reason=None)

    conflicting_features: set[tuple[str, str]] = set()
    for (participant, _), record in selected.items():
        feature_key = (participant, record.feature_name)
        if feature_key in conflicting_features:
            continue
        existing = records[participant].get(record.feature_name)
        if existing is not None:
            # A semantically identical feature from separate sources is not
            # silently merged. Reconciliation can prove identity, but it
            # cannot prove that two values are interchangeable.
            exclusions.append(FeatureExclusion(
                existing.source_receipt_id or "unknown",
                "PROVIDER_FEATURE_CONFLICT",
                existing.source_provider,
                participant,
                record.feature_name,
            ))
            exclusions.append(FeatureExclusion(
                record.source_receipt_id or "unknown",
                "PROVIDER_FEATURE_CONFLICT",
                record.source_provider,
                participant,
                record.feature_name,
            ))
            records[participant].pop(record.feature_name, None)
            conflicting_features.add(feature_key)
            continue
        records[participant][record.feature_name] = record

    for feature_name, definition in definitions.items():
        if definition.normalisation != "RACE_ZSCORE":
            continue
        eligible = [(participant, record) for participant in participant_ids for record in records[participant].values() if record.feature_name == feature_name and record.value is not None]
        normalized = _zscore([record.value for _, record in eligible if record.value is not None])
        for index, (participant, record) in enumerate(eligible):
            records[participant][feature_name] = FeatureRecord(**{**asdict(record), "value": normalized[index]})

    critical_missing = tuple(sorted(
        f"{participant}:{name}" for participant in participant_ids for name, definition in definitions.items()
        if definition.critical and (name not in records[participant] or records[participant][name].value is None)
    ))
    body = {
        "schema_version": FEATURE_GENERATION_VERSION, "race_id": race_id, "code": code, "cutoff": cutoff_text,
        "records": {participant: {name: record.to_dict() for name, record in values.items()} for participant, values in records.items()},
        "exclusions": [asdict(item) for item in exclusions], "critical_missing": list(critical_missing),
    }
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    return FeatureSnapshot(FEATURE_GENERATION_VERSION, race_id, code, cutoff_text, records, tuple(exclusions), critical_missing, digest)
