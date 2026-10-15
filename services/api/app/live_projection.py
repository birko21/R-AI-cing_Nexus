"""Fail-closed projection of approved provider envelopes into the race model.

Provider payloads are deliberately normalised through a small alias map. A
payload that does not contain stable race, time, venue and runner identity is
rejected instead of being guessed into the canonical tables.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from sqlalchemy import Connection, text

from app.betfair_live_projection import parse_betfair_catalogue
from app.provenance import RawEnvelope


class LiveProjectionError(ValueError):
    """Raised when an approved response cannot be reconciled safely."""


@dataclass(frozen=True)
class ProjectedRunner:
    entry_id: str
    participant_id: str
    name: str
    number: int
    status: str
    position: int | None = None


@dataclass(frozen=True)
class ProjectedRace:
    provider: str
    race_id: str
    meeting_id: str
    venue: str
    race_number: int
    scheduled_at: datetime
    field_revision: str
    runners: tuple[ProjectedRunner, ...]
    official: bool


def _text(value: object, label: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)) or not str(value).strip():
        raise LiveProjectionError(f"provider field {label} is missing")
    return str(value).strip()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise LiveProjectionError(f"provider field {label} is not an object")
    return value


def _first(mapping: Mapping[str, object], *keys: str) -> object | None:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def _timestamp(value: object, label: str) -> datetime:
    raw = _text(value, label).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise LiveProjectionError(f"provider field {label} is not an ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise LiveProjectionError(f"provider field {label} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _positive_int(value: object, label: str) -> int:
    try:
        result = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise LiveProjectionError(f"provider field {label} is not a positive integer") from exc
    if result < 1:
        raise LiveProjectionError(f"provider field {label} is not a positive integer")
    return result


def _collection(payload: Mapping[str, object]) -> list[object]:
    for key in ("results", "races", "meetings", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, Mapping):
            nested = _collection(value)
            if nested:
                return nested
    raise LiveProjectionError("provider response contains no supported race collection")


def _race_items(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    items: list[Mapping[str, object]] = []
    for raw in _collection(payload):
        item = _mapping(raw, "race item")
        nested = item.get("races")
        if isinstance(nested, list):
            meeting = item.get("meeting")
            meeting_value = meeting if isinstance(meeting, Mapping) else item
            for child in nested:
                child_mapping = dict(_mapping(child, "race item"))
                child_mapping.setdefault("meeting", meeting_value)
                for key in ("venue", "track", "trackName", "scheduled_at", "scheduledAt", "start_time", "startTime"):
                    if key not in child_mapping and key in item:
                        child_mapping[key] = item[key]
                items.append(child_mapping)
        else:
            items.append(item)
    return items


def _runners(item: Mapping[str, object]) -> list[Mapping[str, object]]:
    for key in ("runners", "entries", "horses", "field", "result", "finishers"):
        value = item.get(key)
        if isinstance(value, list):
            return [_mapping(raw, "runner") for raw in value]
    runner = item.get("runner")
    if isinstance(runner, Mapping):
        return [runner]
    raise LiveProjectionError("race contains no supported runner collection")


def _parse_generic(envelope: RawEnvelope) -> tuple[ProjectedRace, ...]:
    provider = envelope.source_identifier.split(":", 1)[0]
    parsed: list[ProjectedRace] = []
    for item in _race_items(envelope.payload):
        meeting = item.get("meeting")
        meeting_mapping = meeting if isinstance(meeting, Mapping) else {}
        venue = _text(_first(item, "venue", "track", "trackName") or _first(meeting_mapping, "venue", "name", "track"), "venue")
        scheduled_at = _timestamp(
            _first(item, "scheduled_at", "scheduledAt", "start_time", "startTime", "raceStartTime", "start")
            or _first(meeting_mapping, "scheduled_at", "scheduledAt", "date"),
            "scheduled_at",
        )
        race_number = _positive_int(_first(item, "race_number", "raceNumber", "raceNo", "number"), "race_number")
        source_race_id = _first(item, "race_id", "raceId", "raceID", "id")
        race_key = _text(source_race_id, "race_id") if source_race_id is not None else f"{venue}:{scheduled_at.date().isoformat()}:{race_number}"
        source_meeting_id = _first(item, "meeting_id", "meetingId") or _first(meeting_mapping, "meeting_id", "meetingId", "id")
        meeting_key = _text(source_meeting_id, "meeting_id") if source_meeting_id is not None else f"{venue}:{scheduled_at.date().isoformat()}"

        runners: list[ProjectedRunner] = []
        seen_ids: set[str] = set()
        for index, raw_runner in enumerate(_runners(item), start=1):
            source_runner_id = _first(raw_runner, "runner_id", "runnerId", "horse_id", "horseId", "entry_id", "entryId", "id")
            runner_key = _text(source_runner_id, "runner_id") if source_runner_id is not None else None
            name = _text(_first(raw_runner, "name", "runner_name", "runnerName", "horse_name", "horseName"), "runner_name")
            number = _positive_int(_first(raw_runner, "number", "saddlecloth", "runnerNumber", "tabNo") or index, "runner_number")
            source_key = runner_key or f"{name}:{number}"
            entry_id = f"{provider}:race:{race_key}:runner:{source_key}"
            if entry_id in seen_ids:
                raise LiveProjectionError(f"race {race_key} repeats runner identity {source_key}")
            seen_ids.add(entry_id)
            raw_status = _first(raw_runner, "status", "runnerStatus") or "ACTIVE"
            status = str(raw_status).strip().upper()
            status = "SCRATCHED" if status in {"SCRATCHED", "REMOVED", "WITHDRAWN"} else "ACTIVE"
            raw_position = _first(raw_runner, "position", "placing", "finishPosition", "finishingPosition", "place")
            position = _positive_int(raw_position, "position") if raw_position not in (None, "") else None
            runners.append(ProjectedRunner(entry_id, f"{provider}:runner:{source_key}", name, number, status, position))
        if not runners:
            raise LiveProjectionError(f"race {race_key} contains no runners")
        runners = sorted(runners, key=lambda runner: (runner.number, runner.entry_id))
        revision_payload = [runner.__dict__ for runner in runners]
        field_revision = hashlib.sha256(json.dumps(revision_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]
        official = any(runner.position is not None for runner in runners)
        parsed.append(
            ProjectedRace(
                provider,
                f"{provider}:race:{race_key}",
                f"{provider}:meeting:{meeting_key}",
                venue,
                race_number,
                scheduled_at,
                field_revision,
                tuple(runners),
                official,
            )
        )
    return tuple(parsed)


def parse_live_envelope(envelope: RawEnvelope) -> tuple[ProjectedRace, ...]:
    if envelope.data_mode != "LICENSED" or envelope.rights_state != "APPROVED":
        raise LiveProjectionError("live projection requires a licensed, approved envelope")
    if envelope.source_identifier.startswith("betfair-exchange:"):
        catalogue = parse_betfair_catalogue(envelope)
        return tuple(
            ProjectedRace(
                "betfair-exchange", race.race_id, race.meeting_id, race.venue, race.race_number,
                race.scheduled_at, race.field_revision,
                tuple(ProjectedRunner(runner.entry_id, runner.participant_id, runner.name, runner.number, "SCRATCHED" if runner.status == "REMOVED" else "ACTIVE") for runner in race.runners),
                False,
            )
            for race in catalogue.races
        )
    return _parse_generic(envelope)


def project_live_envelope(connection: Connection, envelope: RawEnvelope) -> dict[str, int]:
    races = parse_live_envelope(envelope)
    receipt_id = f"receipt:{envelope.envelope_id}"
    counts = {"races": 0, "entries": 0, "results": 0}
    for race in races:
        connection.execute(text("""
            INSERT INTO meetings (meeting_id, code, name, country, scheduled_at, data_mode, source_receipt_id, first_observed_at)
            VALUES (:meeting_id, 'THOROUGHBRED', :name, 'AUS', :scheduled_at, :data_mode, :source_receipt_id, :first_observed_at)
            ON CONFLICT (meeting_id) DO NOTHING
        """), {"meeting_id": race.meeting_id, "name": race.venue, "scheduled_at": race.scheduled_at, "data_mode": envelope.data_mode, "source_receipt_id": receipt_id, "first_observed_at": envelope.first_observed_at})
        connection.execute(text("""
            INSERT INTO race_revisions (race_id, meeting_id, race_number, status, field_revision, effective_from, first_observed_at, data_mode, source_receipt_id)
            VALUES (:race_id, :meeting_id, :race_number, :status, :field_revision, :effective_from, :first_observed_at, :data_mode, :source_receipt_id)
            ON CONFLICT (race_id, field_revision) DO NOTHING
        """), {"race_id": race.race_id, "meeting_id": race.meeting_id, "race_number": race.race_number, "status": "OFFICIAL" if race.official else "FINAL_FIELDS", "field_revision": race.field_revision, "effective_from": race.scheduled_at, "first_observed_at": envelope.first_observed_at, "data_mode": envelope.data_mode, "source_receipt_id": receipt_id})
        race_revision_id = connection.execute(text("SELECT race_revision_id FROM race_revisions WHERE race_id = :race_id AND field_revision = :field_revision"), {"race_id": race.race_id, "field_revision": race.field_revision}).scalar_one()
        counts["races"] += 1
        placings: dict[str, int] = {}
        scratched: list[str] = []
        for runner in race.runners:
            connection.execute(text("""
                INSERT INTO participants (participant_id, code, name, source_receipt_id, first_observed_at, data_mode)
                VALUES (:participant_id, 'THOROUGHBRED', :name, :source_receipt_id, :first_observed_at, :data_mode)
                ON CONFLICT (participant_id) DO NOTHING
            """), {"participant_id": runner.participant_id, "name": runner.name, "source_receipt_id": receipt_id, "first_observed_at": envelope.first_observed_at, "data_mode": envelope.data_mode})
            connection.execute(text("""
                INSERT INTO entry_revisions (entry_id, race_revision_id, participant_id, number, status, effective_from, first_observed_at, data_mode, source_receipt_id)
                SELECT :entry_id, :race_revision_id, :participant_id, :number, :status, :effective_from, :first_observed_at, :data_mode, :source_receipt_id
                WHERE NOT EXISTS (SELECT 1 FROM entry_revisions WHERE entry_id = :entry_id AND race_revision_id = :race_revision_id)
            """), {"entry_id": runner.entry_id, "race_revision_id": race_revision_id, "participant_id": runner.participant_id, "number": runner.number, "status": runner.status, "effective_from": race.scheduled_at, "first_observed_at": envelope.first_observed_at, "data_mode": envelope.data_mode, "source_receipt_id": receipt_id})
            counts["entries"] += 1
            if runner.position is not None:
                placings[runner.entry_id] = runner.position
            if runner.status == "SCRATCHED":
                scratched.append(runner.entry_id)
        if race.official and placings:
            result_id = f"{race.race_id}:result:{envelope.envelope_id}"
            connection.execute(text("""
                INSERT INTO official_result_revisions (result_id, race_id, field_revision, source_receipt_id, status, observed_at, official_at, placings, dead_heat_groups, scratched_entries, data_mode)
                VALUES (:result_id, :race_id, :field_revision, :source_receipt_id, 'OFFICIAL', :observed_at, :official_at, CAST(:placings AS jsonb), '[]'::jsonb, :scratched_entries, :data_mode)
                ON CONFLICT (result_id) DO NOTHING
            """), {"result_id": result_id, "race_id": race.race_id, "field_revision": race.field_revision, "source_receipt_id": receipt_id, "observed_at": envelope.retrieved_at, "official_at": envelope.retrieved_at, "placings": json.dumps(placings, sort_keys=True), "scratched_entries": scratched, "data_mode": envelope.data_mode})
            counts["results"] += 1
    return counts


