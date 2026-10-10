from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain import DomainInvariantError, RacingCode, VALID_CODES


RaceStatus = Literal["SCHEDULED", "ACCEPTANCES", "FINAL_FIELDS", "OFFICIAL", "ABANDONED", "POSTPONED"]
LifecycleEventType = Literal[
    "ACCEPTANCES",
    "FINAL_FIELDS",
    "SCRATCHING",
    "RESERVE",
    "POSTPONEMENT",
    "OFFICIAL_RESULT",
    "ABANDONED",
    "CORRECTION",
]

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "SCHEDULED": {"ACCEPTANCES", "POSTPONED", "ABANDONED"},
    "ACCEPTANCES": {"FINAL_FIELDS", "POSTPONED", "ABANDONED"},
    "FINAL_FIELDS": {"OFFICIAL", "ABANDONED"},
    "OFFICIAL": set(),
    "POSTPONED": {"SCHEDULED", "ABANDONED"},
    "ABANDONED": set(),
}


class RaceLifecycleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    race_id: str = Field(min_length=1)
    code: RacingCode
    event_type: LifecycleEventType
    status: RaceStatus
    field_revision: str = Field(min_length=1)
    observed_at: datetime
    effective_at: datetime
    payload: dict[str, object] = Field(default_factory=dict)

    def validate_code(self) -> None:
        if self.code not in VALID_CODES:
            raise DomainInvariantError(f"unsupported racing code: {self.code}")


class RaceLifecycle:
    def __init__(self, race_id: str, code: RacingCode) -> None:
        if code not in VALID_CODES:
            raise DomainInvariantError(f"unsupported racing code: {code}")
        self.race_id = race_id
        self.code = code
        self._events: list[RaceLifecycleEvent] = []

    @property
    def events(self) -> tuple[RaceLifecycleEvent, ...]:
        return tuple(self._events)

    @property
    def current_status(self) -> RaceStatus:
        return self._events[-1].status if self._events else "SCHEDULED"

    @property
    def current_field_revision(self) -> str | None:
        return self._events[-1].field_revision if self._events else None

    def append(self, event: RaceLifecycleEvent) -> None:
        event.validate_code()
        if event.race_id != self.race_id or event.code != self.code:
            raise DomainInvariantError("lifecycle event race and code must match the aggregate")
        if self._events and event.observed_at < self._events[-1].observed_at:
            raise DomainInvariantError("lifecycle events must be appended in observed-time order")

        state_change = event.event_type not in {"SCRATCHING", "RESERVE", "CORRECTION"}
        if state_change and event.status not in ALLOWED_TRANSITIONS[self.current_status]:
            raise DomainInvariantError(
                f"invalid race lifecycle transition: {self.current_status} -> {event.status}"
            )
        if not state_change and event.status != self.current_status:
            raise DomainInvariantError("field events must retain the current race status")
        if event.event_type == "OFFICIAL_RESULT" and event.status != "OFFICIAL":
            raise DomainInvariantError("official result events must create OFFICIAL status")
        if event.event_type == "ABANDONED" and event.status != "ABANDONED":
            raise DomainInvariantError("abandoned events must create ABANDONED status")

        self._events.append(event)
