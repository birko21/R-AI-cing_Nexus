from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


RacingCode = str
VALID_CODES = {"THOROUGHBRED", "HARNESS", "GREYHOUND"}


class DomainInvariantError(ValueError):
    pass


def canonical_id(code: RacingCode, source_system: str, source_id: str) -> str:
    if code not in VALID_CODES:
        raise DomainInvariantError(f"unsupported racing code: {code}")
    if not source_system.strip() or not source_id.strip():
        raise DomainInvariantError("source_system and source_id are required; names are not identifiers")
    return f"{code}:{source_system.strip()}:{source_id.strip()}"


class CanonicalEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    code: RacingCode
    source_system: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    name: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_canonical_identity(self):
        expected = canonical_id(self.code, self.source_system, self.source_id)
        if self.entity_id != expected:
            raise DomainInvariantError("entity_id must be code/source-system/source-id namespaced")
        return self


class Participant(CanonicalEntity):
    participant_id: str

    @model_validator(mode="after")
    def validate_participant_identity(self):
        if self.participant_id != self.entity_id:
            raise DomainInvariantError("participant_id must equal the canonical entity_id")
        return self


class Meeting(CanonicalEntity):
    meeting_id: str
    scheduled_at: datetime

    @model_validator(mode="after")
    def validate_meeting_identity(self):
        if self.meeting_id != self.entity_id:
            raise DomainInvariantError("meeting_id must equal the canonical entity_id")
        return self


class Race(CanonicalEntity):
    race_id: str
    meeting_id: str
    race_number: int = Field(gt=0)
    field_revision: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_race_identity(self):
        if self.race_id != self.entity_id:
            raise DomainInvariantError("race_id must equal the canonical entity_id")
        return self


class Entry(CanonicalEntity):
    entry_id: str
    race_id: str
    participant_id: str
    number: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_entry_identity(self):
        if self.entry_id != self.entity_id:
            raise DomainInvariantError("entry_id must equal the canonical entity_id")
        return self


class MarketSelectionMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mapping_id: str
    code: RacingCode
    race_id: str
    field_revision: str = Field(min_length=1)
    entry_id: str
    market_source: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    selection_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def reject_name_only_mapping(self):
        if not self.entry_id or not self.selection_id:
            raise DomainInvariantError("market mappings require exact entry and selection identifiers")
        return self


class DomainRegistry:
    def __init__(self) -> None:
        self.participants: dict[str, Participant] = {}
        self.meetings: dict[str, Meeting] = {}
        self.races: dict[str, Race] = {}
        self.entries: dict[str, Entry] = {}
        self.market_mappings: dict[str, MarketSelectionMapping] = {}

    def add_participant(self, participant: Participant) -> None:
        self._put(self.participants, participant.participant_id, participant)

    def add_meeting(self, meeting: Meeting) -> None:
        self._put(self.meetings, meeting.meeting_id, meeting)

    def add_race(self, race: Race) -> None:
        meeting = self.meetings.get(race.meeting_id)
        if meeting is None:
            raise DomainInvariantError("race must reference an existing meeting")
        if meeting.code != race.code:
            raise DomainInvariantError("race and meeting codes must match")
        self._put(self.races, race.race_id, race)

    def add_entry(self, entry: Entry) -> None:
        race = self.races.get(entry.race_id)
        participant = self.participants.get(entry.participant_id)
        if race is None or participant is None:
            raise DomainInvariantError("entry must reference existing race and participant")
        if race.code != entry.code or participant.code != entry.code:
            raise DomainInvariantError("entry, race and participant codes must match")
        self._put(self.entries, entry.entry_id, entry)

    def add_market_mapping(self, mapping: MarketSelectionMapping) -> None:
        race = self.races.get(mapping.race_id)
        entry = self.entries.get(mapping.entry_id)
        if race is None or entry is None:
            raise DomainInvariantError("market mapping must reference existing race and entry")
        if race.code != mapping.code or entry.code != mapping.code:
            raise DomainInvariantError("market mapping and exact entry codes must match")
        self._put(self.market_mappings, mapping.mapping_id, mapping)

    @staticmethod
    def _put(store: dict[str, object], key: str, value: object) -> None:
        existing = store.get(key)
        if existing is not None and existing != value:
            raise DomainInvariantError(f"canonical identifier collision: {key}")
        store[key] = value
