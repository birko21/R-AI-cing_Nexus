from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain import DomainInvariantError


def require_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainInvariantError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


class BitemporalFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fact_revision_id: str = Field(min_length=1)
    fact_key: str = Field(min_length=1)
    source_event_at: datetime
    published_at: datetime | None = None
    observed_at: datetime
    effective_from: datetime
    effective_to: datetime | None = None
    system_valid_from: datetime
    system_valid_to: datetime | None = None
    source_receipt_id: str = Field(min_length=1)
    receipt_proof: bool
    payload: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_temporal_order(self):
        values = {
            "source_event_at": require_aware(self.source_event_at, "source_event_at"),
            "published_at": require_aware(self.published_at, "published_at") if self.published_at else None,
            "observed_at": require_aware(self.observed_at, "observed_at"),
            "effective_from": require_aware(self.effective_from, "effective_from"),
            "effective_to": require_aware(self.effective_to, "effective_to") if self.effective_to else None,
            "system_valid_from": require_aware(self.system_valid_from, "system_valid_from"),
            "system_valid_to": require_aware(self.system_valid_to, "system_valid_to") if self.system_valid_to else None,
        }
        if values["published_at"] and values["published_at"] < values["source_event_at"]:
            raise DomainInvariantError("published_at cannot precede source_event_at")
        for start_name, end_name in (("effective_from", "effective_to"), ("system_valid_from", "system_valid_to")):
            if values[end_name] and values[end_name] <= values[start_name]:
                raise DomainInvariantError(f"{end_name} must be after {start_name}")
        for field_name, value in values.items():
            object.__setattr__(self, field_name, value)
        return self

    def available_by(self, cutoff: datetime) -> bool:
        cutoff_utc = require_aware(cutoff, "cutoff")
        observed_at = require_aware(self.observed_at, "observed_at")
        published_at = require_aware(self.published_at, "published_at") if self.published_at else None
        if not self.receipt_proof or not self.source_receipt_id:
            return False
        if observed_at > cutoff_utc:
            return False
        if published_at and published_at > cutoff_utc:
            return False
        return True

    def valid_at(self, as_of: datetime) -> bool:
        as_of_utc = require_aware(as_of, "as_of")
        system_valid_from = require_aware(self.system_valid_from, "system_valid_from")
        system_valid_to = require_aware(self.system_valid_to, "system_valid_to") if self.system_valid_to else None
        effective_from = require_aware(self.effective_from, "effective_from")
        effective_to = require_aware(self.effective_to, "effective_to") if self.effective_to else None
        return (
            system_valid_from <= as_of_utc
            and (system_valid_to is None or as_of_utc < system_valid_to)
            and effective_from <= as_of_utc
            and (effective_to is None or as_of_utc < effective_to)
        )


def select_as_of(facts: Iterable[BitemporalFact], as_of: datetime) -> list[BitemporalFact]:
    as_of_utc = require_aware(as_of, "as_of")
    selected: dict[str, BitemporalFact] = {}
    for fact in facts:
        if not fact.available_by(as_of_utc) or not fact.valid_at(as_of_utc):
            continue
        current = selected.get(fact.fact_key)
        if current is None or fact.system_valid_from > current.system_valid_from:
            selected[fact.fact_key] = fact
    return sorted(selected.values(), key=lambda item: item.fact_key)
