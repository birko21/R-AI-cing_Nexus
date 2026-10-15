"""Fail-closed parsing and projection for Betfair market catalogue data.

This is deliberately limited to pre-race Australian thoroughbred catalogue
identity. It does not treat prices, SP, settlement or market-book data as form
features, and it does not create forecasts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re

from sqlalchemy import Connection, text

from app.provenance import RawEnvelope


class BetfairCatalogueParseError(ValueError):
    """Raised when a live catalogue cannot be safely mapped to race identity."""


@dataclass(frozen=True)
class BetfairRunner:
    entry_id: str
    participant_id: str
    selection_id: str
    name: str
    number: int
    status: str


@dataclass(frozen=True)
class BetfairRace:
    race_id: str
    meeting_id: str
    market_id: str
    event_id: str | None
    venue: str
    race_number: int
    scheduled_at: datetime
    field_revision: str
    runners: tuple[BetfairRunner, ...]


@dataclass(frozen=True)
class BetfairCatalogue:
    races: tuple[BetfairRace, ...]


_RACE_NUMBER = re.compile(r"\b(?:R|RACE)\s*0*(\d{1,2})\b", re.IGNORECASE)


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BetfairCatalogueParseError(f"catalogue field {label} is missing")
    return value.strip()


def _identifier(value: object, label: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise BetfairCatalogueParseError(f"catalogue field {label} is missing")
    text_value = str(value).strip()
    if not text_value:
        raise BetfairCatalogueParseError(f"catalogue field {label} is missing")
    return text_value


def _timestamp(value: object, label: str) -> datetime:
    raw = _required_text(value, label).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise BetfairCatalogueParseError(f"catalogue field {label} is not an ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BetfairCatalogueParseError(f"catalogue field {label} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _integer(value: object, label: str) -> int:
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise BetfairCatalogueParseError(f"catalogue field {label} is not a positive integer") from exc
    if number < 1:
        raise BetfairCatalogueParseError(f"catalogue field {label} is not a positive integer")
    return number


def _event(market: Mapping[str, object]) -> Mapping[str, object]:
    value = market.get("event")
    return value if isinstance(value, Mapping) else {}


def _venue(market: Mapping[str, object]) -> str:
    event = _event(market)
    for candidate in (event.get("venue"), event.get("name"), market.get("venue")):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    raise BetfairCatalogueParseError("catalogue event venue/name is missing")


def _race_number(market: Mapping[str, object]) -> int:
    for value in (market.get("marketName"), market.get("description")):
        if isinstance(value, str):
            match = _RACE_NUMBER.search(value)
            if match:
                return int(match.group(1))
    raise BetfairCatalogueParseError("catalogue market name does not contain a race number")


def _runner_number(runner: Mapping[str, object], index: int) -> int:
    metadata = runner.get("metadata")
    if isinstance(metadata, Mapping):
        for key in ("CLOTH_NUMBER", "clothNumber", "runnerNumber"):
            if key in metadata and metadata[key] not in (None, ""):
                return _integer(metadata[key], f"runner metadata {key}")
    if runner.get("sortPriority") not in (None, ""):
        return _integer(runner["sortPriority"], "runner sortPriority")
    return index


def _field_revision(market_id: str, scheduled_at: datetime, runners: tuple[BetfairRunner, ...]) -> str:
    canonical = {
        "market_id": market_id,
        "scheduled_at": scheduled_at.isoformat(),
        "runners": [runner.__dict__ for runner in runners],
    }
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]


def parse_betfair_catalogue(envelope: RawEnvelope) -> BetfairCatalogue:
    if envelope.data_mode != "LICENSED" or envelope.rights_state != "APPROVED":
        raise BetfairCatalogueParseError("Betfair catalogue requires a licensed, approved envelope")
    result = envelope.payload.get("result")
    if not isinstance(result, list):
        if envelope.payload.get("error"):
            raise BetfairCatalogueParseError("Betfair catalogue returned a JSON-RPC error")
        raise BetfairCatalogueParseError("Betfair catalogue result is not a list")

    races: list[BetfairRace] = []
    for market in result:
        if not isinstance(market, Mapping):
            raise BetfairCatalogueParseError("Betfair catalogue contains a non-object market")
        market_id = _identifier(market.get("marketId"), "marketId")
        scheduled_at = _timestamp(market.get("marketStartTime"), "marketStartTime")
        event = _event(market)
        event_id = event.get("id")
        event_id = event_id.strip() if isinstance(event_id, str) and event_id.strip() else None
        venue = _venue(market)
        runners_raw = market.get("runners")
        if not isinstance(runners_raw, list) or not runners_raw:
            raise BetfairCatalogueParseError(f"market {market_id} has no runners")
        runners: list[BetfairRunner] = []
        seen_selection_ids: set[str] = set()
        for index, raw_runner in enumerate(runners_raw, start=1):
            if not isinstance(raw_runner, Mapping):
                raise BetfairCatalogueParseError(f"market {market_id} contains a non-object runner")
            selection_id = _identifier(raw_runner.get("selectionId"), "selectionId")
            if selection_id in seen_selection_ids:
                raise BetfairCatalogueParseError(f"market {market_id} repeats selection {selection_id}")
            seen_selection_ids.add(selection_id)
            name = _required_text(raw_runner.get("runnerName"), "runnerName")
            status = raw_runner.get("runnerStatus", "ACTIVE")
            status = status.strip().upper() if isinstance(status, str) and status.strip() else "ACTIVE"
            if status not in {"ACTIVE", "REMOVED", "WINNER", "LOSER", "PLACED"}:
                status = "ACTIVE"
            entry_id = f"betfair:market:{market_id}:selection:{selection_id}"
            runners.append(BetfairRunner(entry_id, f"betfair:selection:{selection_id}", selection_id, name, _runner_number(raw_runner, index), status))
        normalized_runners = tuple(sorted(runners, key=lambda item: (item.number, item.selection_id)))
        meeting_key = event_id or f"{venue.lower()}:{scheduled_at.date().isoformat()}"
        meeting_id = f"betfair:event:{meeting_key}"
        race_id = f"betfair:market:{market_id}"
        races.append(BetfairRace(race_id, meeting_id, market_id, event_id, venue, _race_number(market), scheduled_at, _field_revision(market_id, scheduled_at, normalized_runners), normalized_runners))
    return BetfairCatalogue(tuple(races))


def project_betfair_catalogue(connection: Connection, envelope: RawEnvelope) -> dict[str, int]:
    catalogue = parse_betfair_catalogue(envelope)
    receipt_id = f"receipt:{envelope.envelope_id}"
    projected_races = 0
    projected_entries = 0
    for race in catalogue.races:
        connection.execute(
            text(
                """
                INSERT INTO meetings (
                    meeting_id, code, name, country, scheduled_at, data_mode,
                    source_receipt_id, first_observed_at
                ) VALUES (
                    :meeting_id, 'THOROUGHBRED', :name, 'AUS', :scheduled_at, :data_mode,
                    :source_receipt_id, :first_observed_at
                ) ON CONFLICT (meeting_id) DO NOTHING
                """
            ),
            {
                "meeting_id": race.meeting_id,
                "name": race.venue,
                "scheduled_at": race.scheduled_at,
                "data_mode": envelope.data_mode,
                "source_receipt_id": receipt_id,
                "first_observed_at": envelope.first_observed_at,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO race_revisions (
                    race_id, meeting_id, race_number, status, field_revision,
                    effective_from, first_observed_at, data_mode, source_receipt_id
                ) VALUES (
                    :race_id, :meeting_id, :race_number, 'ACCEPTANCES', :field_revision,
                    :effective_from, :first_observed_at, :data_mode, :source_receipt_id
                ) ON CONFLICT (race_id, field_revision) DO NOTHING
                """
            ),
            {
                "race_id": race.race_id,
                "meeting_id": race.meeting_id,
                "race_number": race.race_number,
                "field_revision": race.field_revision,
                "effective_from": race.scheduled_at,
                "first_observed_at": envelope.first_observed_at,
                "data_mode": envelope.data_mode,
                "source_receipt_id": receipt_id,
            },
        )
        race_revision_id = connection.execute(
            text("SELECT race_revision_id FROM race_revisions WHERE race_id = :race_id AND field_revision = :field_revision"),
            {"race_id": race.race_id, "field_revision": race.field_revision},
        ).scalar_one()
        projected_races += 1
        for runner in race.runners:
            connection.execute(
                text(
                    """
                    INSERT INTO market_selection_mappings (
                        mapping_id, code, race_id, field_revision, entry_id,
                        market_source, market_id, selection_id
                    ) VALUES (
                        :mapping_id, 'THOROUGHBRED', :race_id, :field_revision,
                        :entry_id, 'BETFAIR_EXCHANGE', :market_id, :selection_id
                    ) ON CONFLICT (market_source, market_id, selection_id) DO NOTHING
                    """
                ),
                {
                    "mapping_id": f"betfair:{race.market_id}:{runner.selection_id}",
                    "race_id": race.race_id,
                    "field_revision": race.field_revision,
                    "entry_id": runner.entry_id,
                    "market_id": race.market_id,
                    "selection_id": runner.selection_id,
                },
            )
        for runner in race.runners:
            connection.execute(
                text(
                    """
                    INSERT INTO participants (
                        participant_id, code, name, source_receipt_id, first_observed_at, data_mode
                    ) VALUES (
                        :participant_id, 'THOROUGHBRED', :name, :source_receipt_id, :first_observed_at, :data_mode
                    ) ON CONFLICT (participant_id) DO NOTHING
                    """
                ),
                {
                    "participant_id": runner.participant_id,
                    "name": runner.name,
                    "source_receipt_id": receipt_id,
                    "first_observed_at": envelope.first_observed_at,
                    "data_mode": envelope.data_mode,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO entry_revisions (
                        entry_id, race_revision_id, participant_id, number, status,
                        effective_from, first_observed_at, data_mode, source_receipt_id
                    )
                    SELECT :entry_id, :race_revision_id, :participant_id, :number, :status,
                           :effective_from, :first_observed_at, :data_mode, :source_receipt_id
                    WHERE NOT EXISTS (
                        SELECT 1 FROM entry_revisions
                        WHERE entry_id = :entry_id AND race_revision_id = :race_revision_id
                    )
                    """
                ),
                {
                    "entry_id": runner.entry_id,
                    "race_revision_id": race_revision_id,
                    "participant_id": runner.participant_id,
                    "number": runner.number,
                    "status": "SCRATCHED" if runner.status == "REMOVED" else "ACTIVE",
                    "effective_from": race.scheduled_at,
                    "first_observed_at": envelope.first_observed_at,
                    "data_mode": envelope.data_mode,
                    "source_receipt_id": receipt_id,
                },
            )
            projected_entries += 1
    return {"races": projected_races, "entries": projected_entries}
