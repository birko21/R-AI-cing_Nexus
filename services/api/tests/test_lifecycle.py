from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain import DomainInvariantError
from app.lifecycle import RaceLifecycle, RaceLifecycleEvent


def event(event_id: str, event_type: str, status: str, revision: str, minute: int) -> RaceLifecycleEvent:
    timestamp = datetime(2026, 1, 1, 0, minute, tzinfo=timezone.utc)
    return RaceLifecycleEvent(
        event_id=event_id,
        race_id="THOROUGHBRED:synthetic:race-1",
        code="THOROUGHBRED",
        event_type=event_type,
        status=status,
        field_revision=revision,
        observed_at=timestamp,
        effective_at=timestamp,
    )


def test_lifecycle_accepts_valid_chain_and_field_addenda() -> None:
    lifecycle = RaceLifecycle("THOROUGHBRED:synthetic:race-1", "THOROUGHBRED")
    lifecycle.append(event("e1", "ACCEPTANCES", "ACCEPTANCES", "r1", 1))
    lifecycle.append(event("e2", "FINAL_FIELDS", "FINAL_FIELDS", "r2", 2))
    lifecycle.append(event("e3", "SCRATCHING", "FINAL_FIELDS", "r3", 3))
    lifecycle.append(event("e4", "OFFICIAL_RESULT", "OFFICIAL", "r3", 4))

    assert lifecycle.current_status == "OFFICIAL"
    assert lifecycle.current_field_revision == "r3"
    assert len(lifecycle.events) == 4


def test_lifecycle_rejects_backwards_transition_and_out_of_order_event() -> None:
    lifecycle = RaceLifecycle("THOROUGHBRED:synthetic:race-1", "THOROUGHBRED")
    lifecycle.append(event("e1", "ACCEPTANCES", "ACCEPTANCES", "r1", 2))
    with pytest.raises(DomainInvariantError, match="invalid race lifecycle"):
        lifecycle.append(event("e2", "FINAL_FIELDS", "SCHEDULED", "r2", 3))
    with pytest.raises(DomainInvariantError, match="observed-time"):
        lifecycle.append(event("e3", "CORRECTION", "ACCEPTANCES", "r3", 1))


def test_lifecycle_is_append_only_and_terminal_statuses_are_fail_closed() -> None:
    lifecycle = RaceLifecycle("THOROUGHBRED:synthetic:race-1", "THOROUGHBRED")
    lifecycle.append(event("e1", "ABANDONED", "ABANDONED", "r1", 1))
    with pytest.raises(DomainInvariantError, match="invalid race lifecycle"):
        lifecycle.append(event("e2", "ACCEPTANCES", "ACCEPTANCES", "r2", 2))
    with pytest.raises(ValidationError, match="Instance is frozen"):
        lifecycle.events[0].status = "SCHEDULED"
