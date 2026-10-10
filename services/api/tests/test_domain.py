import pytest
from pydantic import ValidationError

from app.domain import (
    DomainInvariantError,
    DomainRegistry,
    Entry,
    MarketSelectionMapping,
    Meeting,
    Participant,
    Race,
    canonical_id,
)


def entity_kwargs(code: str, kind: str, source_id: str, name: str) -> dict[str, str]:
    entity_id = canonical_id(code, "synthetic", source_id)
    return {
        "entity_id": entity_id,
        "code": code,
        "source_system": "synthetic",
        "source_id": source_id,
        "name": name,
    }


def test_same_source_ids_are_distinct_across_codes() -> None:
    ids = {canonical_id(code, "synthetic", "same-001") for code in ("THOROUGHBRED", "HARNESS", "GREYHOUND")}
    assert len(ids) == 3
    assert all(identifier.split(":", 1)[0] in {"THOROUGHBRED", "HARNESS", "GREYHOUND"} for identifier in ids)


def test_name_only_or_non_namespaced_identity_is_rejected() -> None:
    with pytest.raises(ValidationError, match="namespaced"):
        Participant(**{**entity_kwargs("THOROUGHBRED", "participant", "runner-1", "Runner"), "entity_id": "Runner", "participant_id": "Runner"})


def test_registry_rejects_cross_code_relationships() -> None:
    registry = DomainRegistry()
    meeting = Meeting(**{**entity_kwargs("THOROUGHBRED", "meeting", "meeting-1", "Demo"), "meeting_id": canonical_id("THOROUGHBRED", "synthetic", "meeting-1"), "scheduled_at": "2026-01-01T00:00:00Z"})
    registry.add_meeting(meeting)
    participant = Participant(**{**entity_kwargs("HARNESS", "participant", "runner-1", "Runner"), "participant_id": canonical_id("HARNESS", "synthetic", "runner-1")})
    registry.add_participant(participant)
    race = Race(**{**entity_kwargs("THOROUGHBRED", "race", "race-1", "Race"), "race_id": canonical_id("THOROUGHBRED", "synthetic", "race-1"), "meeting_id": meeting.meeting_id, "race_number": 1, "field_revision": "r1"})
    registry.add_race(race)

    entry = Entry(**{**entity_kwargs("THOROUGHBRED", "entry", "entry-1", "Runner"), "entry_id": canonical_id("THOROUGHBRED", "synthetic", "entry-1"), "race_id": race.race_id, "participant_id": participant.participant_id, "number": 1})
    with pytest.raises(DomainInvariantError, match="codes must match"):
        registry.add_entry(entry)


def test_market_mapping_requires_exact_entry_and_code() -> None:
    registry = DomainRegistry()
    meeting = Meeting(**{**entity_kwargs("THOROUGHBRED", "meeting", "meeting-1", "Demo"), "meeting_id": canonical_id("THOROUGHBRED", "synthetic", "meeting-1"), "scheduled_at": "2026-01-01T00:00:00Z"})
    participant = Participant(**{**entity_kwargs("THOROUGHBRED", "participant", "runner-1", "Runner"), "participant_id": canonical_id("THOROUGHBRED", "synthetic", "runner-1")})
    race = Race(**{**entity_kwargs("THOROUGHBRED", "race", "race-1", "Race"), "race_id": canonical_id("THOROUGHBRED", "synthetic", "race-1"), "meeting_id": meeting.meeting_id, "race_number": 1, "field_revision": "r1"})
    entry = Entry(**{**entity_kwargs("THOROUGHBRED", "entry", "entry-1", "Runner"), "entry_id": canonical_id("THOROUGHBRED", "synthetic", "entry-1"), "race_id": race.race_id, "participant_id": participant.participant_id, "number": 1})
    registry.add_meeting(meeting)
    registry.add_participant(participant)
    registry.add_race(race)
    registry.add_entry(entry)
    mapping = MarketSelectionMapping(mapping_id="map-1", code="HARNESS", race_id=race.race_id, field_revision="r1", entry_id=entry.entry_id, market_source="synthetic", market_id="market-1", selection_id="selection-1")
    with pytest.raises(DomainInvariantError, match="codes must match"):
        registry.add_market_mapping(mapping)
