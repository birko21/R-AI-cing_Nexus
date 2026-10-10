"""Descriptive thoroughbred specialist features with explicit missingness."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from collections.abc import Iterable

from app.features import FeatureValue


THOROUGHBRED_FEATURE_SCHEMA_VERSION = "thoroughbred-features-v1"
SPECIALIST_FEATURES = (
    "class_match_rate", "distance_match_rate", "track_going_match_rate",
    "barrier_position", "weight_kg", "pace_rating", "sectional_time",
)


@dataclass(frozen=True)
class ThoroughbredFact:
    participant_id: str
    observed_at: datetime
    source_receipt_id: str
    class_band: str | None = None
    distance: int | None = None
    track_going: str | None = None
    barrier: int | None = None
    weight_kg: float | None = None
    pace_rating: float | None = None
    sectional_time: float | None = None


@dataclass(frozen=True)
class ThoroughbredFeatureSnapshot:
    schema_version: str
    race_id: str
    participant_id: str
    cutoff: str
    target_class: str | None
    target_distance: int | None
    target_track_going: str | None
    data_mode: str
    features: dict[str, FeatureValue]
    included_receipt_ids: tuple[str, ...]
    excluded_future_receipt_ids: tuple[str, ...]
    attribution_status: str
    snapshot_hash: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["features"] = {
            name: {**asdict(value), "source_receipt_ids": list(value.source_receipt_ids)}
            for name, value in self.features.items()
        }
        payload["included_receipt_ids"] = list(self.included_receipt_ids)
        payload["excluded_future_receipt_ids"] = list(self.excluded_future_receipt_ids)
        return payload


def _cutoff_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("cutoff must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _missing(reason: str, receipts: tuple[str, ...]) -> FeatureValue:
    return FeatureValue(value=None, missing=True, missing_reason=reason, source_receipt_ids=receipts)


def materialize_thoroughbred_features(
    *, race_id: str, participant_id: str, cutoff: datetime,
    target_class: str | None, target_distance: int | None, target_track_going: str | None,
    facts: Iterable[ThoroughbredFact], data_mode: str = "SYNTHETIC_ONLY",
) -> ThoroughbredFeatureSnapshot:
    """Return descriptive features observed before cutoff; never causal attribution."""

    if data_mode not in {"SYNTHETIC_ONLY", "SCRAPED_PUBLIC"}:
        raise ValueError("thoroughbred feature data_mode is unsupported")
    cutoff_iso = _cutoff_text(cutoff)
    participant_facts = tuple(fact for fact in facts if fact.participant_id == participant_id)
    included = tuple(sorted((fact for fact in participant_facts if fact.observed_at < cutoff), key=lambda fact: fact.observed_at))
    excluded = tuple(sorted((fact for fact in participant_facts if fact.observed_at >= cutoff), key=lambda fact: fact.observed_at))
    included_receipts = tuple(fact.source_receipt_id for fact in included)
    excluded_receipts = tuple(fact.source_receipt_id for fact in excluded)
    features: dict[str, FeatureValue] = {}

    if not included:
        features = {name: _missing("NO_PRE_CUTOFF_SUPPORT", ()) for name in SPECIALIST_FEATURES}
    else:
        class_facts = tuple(fact for fact in included if fact.class_band)
        distance_facts = tuple(fact for fact in included if fact.distance is not None and fact.distance > 0)
        going_facts = tuple(fact for fact in included if fact.track_going)
        if target_class is None:
            features["class_match_rate"] = _missing("MISSING_TARGET_CLASS", included_receipts)
        elif class_facts:
            features["class_match_rate"] = FeatureValue(sum(fact.class_band == target_class for fact in class_facts) / len(class_facts), False, None, tuple(fact.source_receipt_id for fact in class_facts))
        else:
            features["class_match_rate"] = _missing("MISSING_CLASS", included_receipts)
        if target_distance is None or target_distance <= 0:
            features["distance_match_rate"] = _missing("MISSING_TARGET_DISTANCE", included_receipts)
        elif distance_facts:
            features["distance_match_rate"] = FeatureValue(sum(fact.distance == target_distance for fact in distance_facts) / len(distance_facts), False, None, tuple(fact.source_receipt_id for fact in distance_facts))
        else:
            features["distance_match_rate"] = _missing("MISSING_DISTANCE", included_receipts)
        if target_track_going is None:
            features["track_going_match_rate"] = _missing("MISSING_TARGET_TRACK_GOING", included_receipts)
        elif going_facts:
            features["track_going_match_rate"] = FeatureValue(sum(fact.track_going == target_track_going for fact in going_facts) / len(going_facts), False, None, tuple(fact.source_receipt_id for fact in going_facts))
        else:
            features["track_going_match_rate"] = _missing("MISSING_TRACK_GOING", included_receipts)
        for name, attribute, reason in (
            ("barrier_position", "barrier", "MISSING_BARRIER"),
            ("weight_kg", "weight_kg", "MISSING_WEIGHT"),
            ("pace_rating", "pace_rating", "MISSING_PACE"),
            ("sectional_time", "sectional_time", "MISSING_SECTIONAL"),
        ):
            available = tuple(fact for fact in included if getattr(fact, attribute) is not None)
            if available:
                latest = available[-1]
                features[name] = FeatureValue(float(getattr(latest, attribute)), False, None, (latest.source_receipt_id,))
            else:
                features[name] = _missing(reason, included_receipts)

    body = {
        "schema_version": THOROUGHBRED_FEATURE_SCHEMA_VERSION, "race_id": race_id, "participant_id": participant_id,
        "cutoff": cutoff_iso, "target_class": target_class, "target_distance": target_distance,
        "target_track_going": target_track_going, "data_mode": data_mode,
        "features": {name: asdict(value) for name, value in features.items()},
        "included_receipt_ids": list(included_receipts), "excluded_future_receipt_ids": list(excluded_receipts),
        "attribution_status": "DESCRIPTIVE_ASSOCIATION_ONLY",
    }
    snapshot_hash = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return ThoroughbredFeatureSnapshot(
        THOROUGHBRED_FEATURE_SCHEMA_VERSION, race_id, participant_id, cutoff_iso, target_class, target_distance,
        target_track_going, data_mode, features, included_receipts, excluded_receipts,
        "DESCRIPTIVE_ASSOCIATION_ONLY", snapshot_hash,
    )
