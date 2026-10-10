"""Versioned, provenance-preserving feature materialization."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from collections.abc import Iterable, Mapping


FEATURE_SCHEMA_VERSION = "features-v1"
SUPPORTED_CODES = frozenset({"THOROUGHBRED", "HARNESS", "GREYHOUND"})
COMMON_FEATURES = ("runs_count", "mean_finish_position", "best_finish_position")
CODE_FEATURES: dict[str, tuple[str, ...]] = {
    "THOROUGHBRED": ("distance_match_rate", "finish_consistency"),
    "HARNESS": ("distance_match_rate", "recent_finish_rate"),
    "GREYHOUND": ("distance_match_rate", "recent_finish_rate"),
}


@dataclass(frozen=True)
class HistoricalRunFact:
    participant_id: str
    code: str
    observed_at: datetime
    distance: int | None
    finish_position: int | None
    source_receipt_id: str


@dataclass(frozen=True)
class FeatureValue:
    value: float | None
    missing: bool
    missing_reason: str | None
    source_receipt_ids: tuple[str, ...]


@dataclass(frozen=True)
class FeatureSnapshot:
    schema_version: str
    race_id: str
    participant_id: str
    code: str
    cutoff: str
    target_distance: int | None
    data_mode: str
    features: dict[str, FeatureValue]
    included_receipt_ids: tuple[str, ...]
    excluded_future_receipt_ids: tuple[str, ...]
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


def _normalise_cutoff(cutoff: datetime) -> str:
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("cutoff must be timezone-aware")
    return cutoff.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash_snapshot(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _missing(reason: str, receipt_ids: tuple[str, ...] = ()) -> FeatureValue:
    return FeatureValue(value=None, missing=True, missing_reason=reason, source_receipt_ids=receipt_ids)


def materialize_feature_snapshot(
    *,
    race_id: str,
    participant_id: str,
    code: str,
    cutoff: datetime,
    target_distance: int | None,
    facts: Iterable[HistoricalRunFact],
    data_mode: str = "SYNTHETIC_ONLY",
) -> FeatureSnapshot:
    """Materialize features from facts strictly observed before ``cutoff``."""

    if code not in SUPPORTED_CODES:
        raise ValueError(f"unsupported feature code: {code}")
    if data_mode not in {"SYNTHETIC_ONLY", "SCRAPED_PUBLIC"}:
        raise ValueError("feature data_mode is unsupported")
    cutoff_text = _normalise_cutoff(cutoff)
    participant_facts = tuple(fact for fact in facts if fact.participant_id == participant_id and fact.code == code)
    included = tuple(sorted((fact for fact in participant_facts if fact.observed_at < cutoff), key=lambda fact: fact.observed_at))
    excluded_future = tuple(sorted((fact for fact in participant_facts if fact.observed_at >= cutoff), key=lambda fact: fact.observed_at))
    included_receipts = tuple(fact.source_receipt_id for fact in included)
    excluded_receipts = tuple(fact.source_receipt_id for fact in excluded_future)
    valid_positions = tuple(fact.finish_position for fact in included if fact.finish_position is not None and fact.finish_position > 0)
    valid_distances = tuple(fact for fact in included if fact.distance is not None and fact.distance > 0)
    features: dict[str, FeatureValue] = {}

    if not included:
        for name in COMMON_FEATURES + CODE_FEATURES[code]:
            features[name] = _missing("NO_PRE_CUTOFF_SUPPORT")
    else:
        features["runs_count"] = FeatureValue(float(len(included)), False, None, included_receipts)
        if valid_positions:
            features["mean_finish_position"] = FeatureValue(sum(valid_positions) / len(valid_positions), False, None, included_receipts)
            features["best_finish_position"] = FeatureValue(float(min(valid_positions)), False, None, included_receipts)
        else:
            features["mean_finish_position"] = _missing("MISSING_FINISH_POSITION", included_receipts)
            features["best_finish_position"] = _missing("MISSING_FINISH_POSITION", included_receipts)
        if target_distance is None or target_distance <= 0:
            features["distance_match_rate"] = _missing("MISSING_TARGET_DISTANCE", included_receipts)
        elif valid_distances:
            matches = sum(fact.distance == target_distance for fact in valid_distances)
            features["distance_match_rate"] = FeatureValue(matches / len(valid_distances), False, None, included_receipts)
        else:
            features["distance_match_rate"] = _missing("MISSING_DISTANCE", included_receipts)
        if code == "THOROUGHBRED":
            if len(valid_positions) >= 2:
                mean = sum(valid_positions) / len(valid_positions)
                variance = sum((position - mean) ** 2 for position in valid_positions) / len(valid_positions)
                features["finish_consistency"] = FeatureValue(1.0 / (1.0 + variance), False, None, included_receipts)
            else:
                features["finish_consistency"] = _missing("INSUFFICIENT_FINISH_SUPPORT", included_receipts)
        else:
            if valid_positions:
                recent = valid_positions[-1]
                features["recent_finish_rate"] = FeatureValue(1.0 / recent, False, None, included_receipts)
            else:
                features["recent_finish_rate"] = _missing("MISSING_FINISH_POSITION", included_receipts)

    snapshot_body = {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "race_id": race_id,
        "participant_id": participant_id,
        "code": code,
        "cutoff": cutoff_text,
        "target_distance": target_distance,
        "data_mode": data_mode,
        "features": {name: asdict(value) for name, value in features.items()},
        "included_receipt_ids": list(included_receipts),
        "excluded_future_receipt_ids": list(excluded_receipts),
    }
    return FeatureSnapshot(
        schema_version=FEATURE_SCHEMA_VERSION,
        race_id=race_id,
        participant_id=participant_id,
        code=code,
        cutoff=cutoff_text,
        target_distance=target_distance,
        data_mode=data_mode,
        features=features,
        included_receipt_ids=included_receipts,
        excluded_future_receipt_ids=excluded_receipts,
        snapshot_hash=_hash_snapshot(snapshot_body),
    )


def materialize_feature_manifest(snapshots: Iterable[FeatureSnapshot]) -> dict[str, object]:
    records = [snapshot.to_dict() for snapshot in snapshots]
    return {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "record_count": len(records),
        "records": records,
        "data_mode": "SYNTHETIC_ONLY",
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
    }
