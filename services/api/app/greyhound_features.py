"""Greyhound specialist features and authorised reserve recomputation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json


GREYHOUND_FEATURES = ("box", "first_split", "early_acceleration", "bend_run_line", "grade", "trouble", "interference")


@dataclass(frozen=True)
class GreyhoundFact:
    participant_id: str
    observed_at: datetime
    source_receipt_id: str
    box: int | None = None
    first_split: float | None = None
    early_acceleration: float | None = None
    bend_run_line: str | None = None
    grade: str | None = None
    trouble: str | None = None
    interference: str | None = None


@dataclass(frozen=True)
class GreyhoundValue:
    value: str | float | int | None
    missing: bool
    missing_reason: str | None
    source_receipt_ids: tuple[str, ...]


@dataclass(frozen=True)
class GreyhoundSnapshot:
    schema_version: str
    race_id: str
    participant_id: str
    cutoff: str
    data_mode: str
    features: dict[str, GreyhoundValue]
    included_receipt_ids: tuple[str, ...]
    excluded_future_receipt_ids: tuple[str, ...]
    recomputed_features: tuple[str, ...]
    snapshot_hash: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["features"] = {name: {**asdict(value), "source_receipt_ids": list(value.source_receipt_ids)} for name, value in self.features.items()}
        payload["included_receipt_ids"] = list(self.included_receipt_ids)
        payload["excluded_future_receipt_ids"] = list(self.excluded_future_receipt_ids)
        payload["recomputed_features"] = list(self.recomputed_features)
        return payload


def _hash(snapshot: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _materialize_body(*, race_id: str, participant_id: str, cutoff: datetime, facts: tuple[GreyhoundFact, ...], data_mode: str, recomputed: tuple[str, ...] = ()) -> GreyhoundSnapshot:
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("cutoff must be timezone-aware")
    if data_mode not in {"SYNTHETIC_ONLY", "SCRAPED_PUBLIC"}:
        raise ValueError("greyhound feature data_mode is unsupported")
    cutoff_iso = cutoff.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    included = tuple(sorted((fact for fact in facts if fact.participant_id == participant_id and fact.observed_at < cutoff), key=lambda fact: fact.observed_at))
    excluded = tuple(sorted((fact for fact in facts if fact.participant_id == participant_id and fact.observed_at >= cutoff), key=lambda fact: fact.observed_at))
    receipts = tuple(fact.source_receipt_id for fact in included)
    future = tuple(fact.source_receipt_id for fact in excluded)
    latest = included[-1] if included else None
    features: dict[str, GreyhoundValue] = {}
    for name in GREYHOUND_FEATURES:
        value = getattr(latest, name) if latest is not None else None
        features[name] = GreyhoundValue(value, value is None, None if value is not None else ("NO_PRE_CUTOFF_SUPPORT" if latest is None else f"MISSING_{name.upper()}"), (latest.source_receipt_id,) if value is not None and latest is not None else receipts)
    body = {
        "schema_version": "greyhound-features-v1", "race_id": race_id, "participant_id": participant_id,
        "cutoff": cutoff_iso, "data_mode": data_mode, "features": {key: asdict(value) for key, value in features.items()},
        "included_receipt_ids": list(receipts), "excluded_future_receipt_ids": list(future), "recomputed_features": list(recomputed),
    }
    return GreyhoundSnapshot("greyhound-features-v1", race_id, participant_id, cutoff_iso, data_mode, features, receipts, future, recomputed, _hash(body))


def materialize_greyhound_features(*, race_id: str, participant_id: str, cutoff: datetime, facts: tuple[GreyhoundFact, ...], data_mode: str = "SYNTHETIC_ONLY") -> GreyhoundSnapshot:
    return _materialize_body(race_id=race_id, participant_id=participant_id, cutoff=cutoff, facts=facts, data_mode=data_mode)


def activate_reserve(snapshot: GreyhoundSnapshot, reserve_fact: GreyhoundFact, *, authorised_features: frozenset[str]) -> GreyhoundSnapshot:
    """Recompute only explicitly authorised features after reserve activation."""

    unknown = authorised_features - set(GREYHOUND_FEATURES)
    if unknown:
        raise ValueError(f"unsupported authorised features: {sorted(unknown)}")
    features = dict(snapshot.features)
    for name in authorised_features:
        value = getattr(reserve_fact, name)
        features[name] = GreyhoundValue(value, value is None, None if value is not None else f"MISSING_{name.upper()}", (reserve_fact.source_receipt_id,) if value is not None else ())
    body = {
        **snapshot.to_dict(), "features": {key: asdict(value) for key, value in features.items()},
        "recomputed_features": sorted(authorised_features),
    }
    return GreyhoundSnapshot(
        snapshot.schema_version, snapshot.race_id, snapshot.participant_id, snapshot.cutoff, snapshot.data_mode,
        features, snapshot.included_receipt_ids, snapshot.excluded_future_receipt_ids, tuple(sorted(authorised_features)), _hash(body),
    )
