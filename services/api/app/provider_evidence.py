"""Typed provider-evidence records that never grant runtime activation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Literal

from app.provenance import DataMode, RightsState


EvidenceStatus = Literal["OBSERVED", "NOT_EVIDENCED", "BLOCKED"]


@dataclass(frozen=True)
class ProviderEvidenceRecord:
    evidence_id: str
    provider_id: str
    capability: str
    source_reference: str
    observed_at: datetime
    evidence_status: EvidenceStatus
    data_mode: DataMode
    rights_state: RightsState
    notes: str
    schema_version: str = "provider-evidence-v1"

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.evidence_id, self.provider_id, self.capability, self.source_reference, self.notes)):
            raise ValueError("provider evidence identity, source and notes are required")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("provider evidence observed_at must be timezone-aware")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["observed_at"] = self.observed_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return payload


class ProviderEvidenceRegistry:
    """Append-only evidence index with deliberately no activation operation."""

    def __init__(self) -> None:
        self._records: dict[str, ProviderEvidenceRecord] = {}

    def register(self, record: ProviderEvidenceRecord) -> None:
        existing = self._records.get(record.evidence_id)
        if existing is not None and existing != record:
            raise ValueError(f"provider evidence {record.evidence_id} is immutable")
        self._records[record.evidence_id] = record

    def records(self) -> tuple[ProviderEvidenceRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def snapshot(self) -> dict[str, object]:
        return {
            "schema_version": "provider-evidence-registry-v1",
            "activation_authority": "NONE",
            "records": [record.to_dict() for record in self.records()],
            "note": "Evidence records describe observed capability only; they cannot enable a provider or grant rights.",
        }
