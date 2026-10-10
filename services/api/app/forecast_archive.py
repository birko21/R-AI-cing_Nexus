"""Canonical immutable forecast manifests and replay checks."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from collections.abc import Mapping, Sequence


class ImmutableArchiveError(ValueError):
    """Raised when an existing forecast ID is changed or a manifest is invalid."""


@dataclass(frozen=True)
class ForecastInvalidation:
    forecast_id: str
    race_id: str
    prior_field_revision: str
    new_field_revision: str
    event_type: str
    reason: str
    invalidated_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "forecast_id": self.forecast_id,
            "race_id": self.race_id,
            "prior_field_revision": self.prior_field_revision,
            "new_field_revision": self.new_field_revision,
            "event_type": self.event_type,
            "reason": self.reason,
            "invalidated_at": self.invalidated_at,
        }


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ForecastManifest:
    forecast_id: str
    race_id: str
    field_revision: str
    cutoff: str
    feature_snapshot: dict[str, object]
    feature_snapshot_hash: str
    model_hash: str
    active_runner_hash: str
    data_mode: str
    diagnostic_flags: tuple[str, ...]
    output: object
    manifest_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "forecast_id": self.forecast_id,
            "race_id": self.race_id,
            "field_revision": self.field_revision,
            "cutoff": self.cutoff,
            "feature_snapshot": deepcopy(self.feature_snapshot),
            "feature_snapshot_hash": self.feature_snapshot_hash,
            "model_hash": self.model_hash,
            "active_runner_hash": self.active_runner_hash,
            "data_mode": self.data_mode,
            "diagnostic_flags": list(self.diagnostic_flags),
            "output": deepcopy(self.output),
            "manifest_hash": self.manifest_hash,
        }


def create_forecast_manifest(
    *,
    forecast_id: str,
    race_id: str,
    field_revision: str,
    cutoff: str,
    feature_snapshot: Mapping[str, object],
    model_descriptor: Mapping[str, object],
    active_runner_ids: Sequence[str],
    data_mode: str,
    diagnostic_flags: Sequence[str],
    output: object,
) -> ForecastManifest:
    """Create a hash-addressed manifest from frozen inputs and output."""

    if not all((forecast_id, race_id, field_revision, cutoff, data_mode)):
        raise ValueError("forecast manifest identity fields are required")
    if data_mode not in {"SYNTHETIC_ONLY", "SCRAPED_PUBLIC"}:
        raise ValueError("forecast manifest data_mode is unsupported")
    if len(set(active_runner_ids)) != len(active_runner_ids):
        raise ValueError("active runner IDs must be unique")
    feature_copy = deepcopy(dict(feature_snapshot))
    feature_hash = _sha256(feature_copy)
    model_hash = _sha256(dict(model_descriptor))
    runner_hash = _sha256(list(active_runner_ids))
    identity = {
        "forecast_id": forecast_id,
        "race_id": race_id,
        "field_revision": field_revision,
        "cutoff": cutoff,
        "feature_snapshot_hash": feature_hash,
        "model_hash": model_hash,
        "active_runner_hash": runner_hash,
        "data_mode": data_mode,
        "diagnostic_flags": list(diagnostic_flags),
        "output": output,
    }
    return ForecastManifest(
        forecast_id=forecast_id, race_id=race_id, field_revision=field_revision, cutoff=cutoff,
        feature_snapshot=feature_copy, feature_snapshot_hash=feature_hash, model_hash=model_hash,
        active_runner_hash=runner_hash, data_mode=data_mode,
        diagnostic_flags=tuple(diagnostic_flags), output=deepcopy(output), manifest_hash=_sha256(identity),
    )


def verify_manifest(manifest: Mapping[str, object]) -> None:
    """Verify all derived hashes and the immutable manifest hash."""

    required = {
        "forecast_id", "race_id", "field_revision", "cutoff", "feature_snapshot", "feature_snapshot_hash",
        "model_hash", "active_runner_hash", "data_mode", "diagnostic_flags", "output", "manifest_hash",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ImmutableArchiveError(f"manifest missing fields: {missing}")
    if manifest["feature_snapshot_hash"] != _sha256(manifest["feature_snapshot"]):
        raise ImmutableArchiveError("feature snapshot hash mismatch")
    identity = {key: manifest[key] for key in (
        "forecast_id", "race_id", "field_revision", "cutoff", "feature_snapshot_hash", "model_hash",
        "active_runner_hash", "data_mode", "diagnostic_flags", "output",
    )}
    if manifest["manifest_hash"] != _sha256(identity):
        raise ImmutableArchiveError("manifest hash mismatch")


class ForecastArchive:
    """In-memory append-only archive used by the local MVP and replay tests."""

    def __init__(self) -> None:
        self._records: dict[str, str] = {}
        self._invalidations: dict[str, str] = {}

    def append(self, manifest: ForecastManifest) -> None:
        payload = _canonical(manifest.to_dict())
        existing = self._records.get(manifest.forecast_id)
        if existing is not None and existing != payload:
            raise ImmutableArchiveError(f"forecast {manifest.forecast_id} is immutable")
        self._records[manifest.forecast_id] = payload

    def append_ready(self, manifest: ForecastManifest, *, forecast_status: str) -> None:
        if forecast_status != "READY":
            raise ImmutableArchiveError("abstained forecast cannot become an active archive record")
        self.append(manifest)

    def get(self, forecast_id: str) -> dict[str, object]:
        if forecast_id not in self._records:
            raise KeyError(forecast_id)
        record = json.loads(self._records[forecast_id])
        verify_manifest(record)
        return record

    def replay_matches(self, forecast_id: str, output: object) -> bool:
        archived = self.get(forecast_id)
        return _canonical(archived["output"]) == _canonical(output)

    def invalidate(
        self,
        forecast_id: str,
        *,
        new_field_revision: str,
        reason: str,
        invalidated_at: str,
        event_type: str = "SCRATCHING",
    ) -> ForecastInvalidation:
        record = self.get(forecast_id)
        prior_revision = record["field_revision"]
        if prior_revision == new_field_revision:
            raise ImmutableArchiveError("forecast invalidation requires a new field revision")
        event = ForecastInvalidation(
            forecast_id=forecast_id, race_id=record["race_id"], prior_field_revision=prior_revision,
            new_field_revision=new_field_revision, event_type=event_type, reason=reason,
            invalidated_at=invalidated_at,
        )
        payload = _canonical(event.to_dict())
        existing = self._invalidations.get(forecast_id)
        if existing is not None and existing != payload:
            raise ImmutableArchiveError(f"forecast {forecast_id} invalidation is immutable")
        self._invalidations[forecast_id] = payload
        return event

    def get_invalidation(self, forecast_id: str) -> dict[str, str]:
        if forecast_id not in self._invalidations:
            raise KeyError(forecast_id)
        return json.loads(self._invalidations[forecast_id])

    def is_current(self, forecast_id: str, current_field_revision: str) -> bool:
        record = self.get(forecast_id)
        return record["field_revision"] == current_field_revision and forecast_id not in self._invalidations

    def __len__(self) -> int:
        return len(self._records)
