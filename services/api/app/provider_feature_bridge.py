"""Strict bridge from provider raw envelopes to historical feature observations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Literal

from app.historical_features import FeatureObservation, RacingCode
from app.provenance import RawEnvelope


ProviderFeatureQuarantineReason = Literal[
    "UNKNOWN_TIMESTAMP",
    "RETENTION_UNSPECIFIED",
    "RIGHTS_NOT_APPROVED",
    "POST_CUTOFF",
    "INVALID_PROVIDER_FEATURE",
]


@dataclass(frozen=True)
class ProviderFeatureQuarantine:
    envelope_id: str
    reason: ProviderFeatureQuarantineReason
    detail: str
    feature_name: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderFeatureBridgeResult:
    observations: tuple[FeatureObservation, ...]
    quarantines: tuple[ProviderFeatureQuarantine, ...]


def _timestamp(value: object, *, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field_name} is not a valid timestamp") from exc
    else:
        raise ValueError(f"{field_name} is unknown")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} is not timezone-aware")
    return parsed.astimezone(timezone.utc)


def bridge_provider_feature_observations(
    envelope: RawEnvelope,
    *,
    provider_id: str,
    dataset_reference: str,
    code: RacingCode,
    race_id: str,
    cutoff: datetime,
) -> ProviderFeatureBridgeResult:
    """Convert only eligible, rights-aware provider rows into feature observations."""

    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("feature cutoff must be timezone-aware")
    cutoff_utc = cutoff.astimezone(timezone.utc)
    raw_rows = envelope.payload.get("feature_observations")
    if not isinstance(raw_rows, list):
        return ProviderFeatureBridgeResult((), (ProviderFeatureQuarantine(
            envelope.envelope_id, "INVALID_PROVIDER_FEATURE", "feature_observations must be a list"
        ),))

    observations: list[FeatureObservation] = []
    quarantines: list[ProviderFeatureQuarantine] = []
    for raw_row in raw_rows:
        if not isinstance(raw_row, Mapping):
            quarantines.append(ProviderFeatureQuarantine(envelope.envelope_id, "INVALID_PROVIDER_FEATURE", "feature row must be an object"))
            continue
        feature_name = raw_row.get("feature_name")
        feature_label = feature_name if isinstance(feature_name, str) else None
        try:
            observed_at = _timestamp(raw_row.get("observed_at"), field_name="observed_at")
            eligible_at = _timestamp(raw_row.get("pre_race_eligible_at"), field_name="pre_race_eligible_at")
            published_raw = raw_row.get("published_at", envelope.published_at)
            published_at = None if published_raw is None else _timestamp(published_raw, field_name="published_at")
        except ValueError as exc:
            quarantines.append(ProviderFeatureQuarantine(envelope.envelope_id, "UNKNOWN_TIMESTAMP", str(exc), feature_label))
            continue
        if envelope.rights_state not in {"SYNTHETIC", "APPROVED"}:
            quarantines.append(ProviderFeatureQuarantine(envelope.envelope_id, "RIGHTS_NOT_APPROVED", "provider envelope rights are not usable", feature_label))
            continue
        retention_class = raw_row.get("retention_class")
        if not isinstance(retention_class, str) or not retention_class.strip():
            quarantines.append(ProviderFeatureQuarantine(envelope.envelope_id, "RETENTION_UNSPECIFIED", "retention_class is required", feature_label))
            continue
        if envelope.retrieved_at > cutoff_utc or observed_at > cutoff_utc or eligible_at > cutoff_utc or (published_at is not None and published_at > cutoff_utc):
            quarantines.append(ProviderFeatureQuarantine(envelope.envelope_id, "POST_CUTOFF", "source or retrieval timestamp is not eligible by cutoff", feature_label))
            continue
        try:
            participant_id = raw_row["participant_id"]
            provider_participant_id = raw_row["provider_participant_id"]
            unit = raw_row["unit"]
            if not all(isinstance(value, str) and value.strip() for value in (feature_name, participant_id, provider_participant_id, unit)):
                raise ValueError("feature identity and unit are required")
            value = raw_row.get("value")
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
                raise ValueError("feature value must be numeric or null")
            identity_evidence = raw_row.get("identity_evidence", "NAME_ONLY")
            if identity_evidence not in {"EXACT", "RECONCILED", "NAME_ONLY"}:
                raise ValueError("identity_evidence is unsupported")
            observations.append(FeatureObservation(
                provider_id=provider_id,
                dataset_reference=dataset_reference,
                code=code,
                race_id=race_id,
                participant_id=participant_id,
                provider_participant_id=provider_participant_id,
                feature_name=feature_name,
                value=None if value is None else float(value),
                unit=unit,
                observed_at=observed_at,
                published_at=published_at,
                retrieved_at=envelope.retrieved_at,
                pre_race_eligible_at=eligible_at,
                source_receipt_id=envelope.envelope_id,
                rights_state=envelope.rights_state,
                retention_class=retention_class,
                quality_state=raw_row.get("quality_state", "VALID"),
                identity_link_id=raw_row.get("identity_link_id"),
                identity_evidence=identity_evidence,
            ))
        except (KeyError, TypeError, ValueError) as exc:
            quarantines.append(ProviderFeatureQuarantine(envelope.envelope_id, "INVALID_PROVIDER_FEATURE", str(exc), feature_label))
    return ProviderFeatureBridgeResult(tuple(observations), tuple(quarantines))
