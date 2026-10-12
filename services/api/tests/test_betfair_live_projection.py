from datetime import datetime, timezone

import pytest

from app.betfair_live_projection import BetfairCatalogueParseError, parse_betfair_catalogue
from app.provenance import RawEnvelope, payload_sha256


def envelope(payload):
    now = datetime(2026, 10, 12, tzinfo=timezone.utc)
    return RawEnvelope(
        envelope_id="catalogue-1",
        source_identifier="betfair-exchange:GET_MARKETS",
        payload=payload,
        payload_sha256=payload_sha256(payload),
        schema_version="provider-response-v1",
        retrieved_at=now,
        first_observed_at=now,
        data_mode="LICENSED",
        rights_state="APPROVED",
        licence_reference="owner-record:rights",
    )


def test_betfair_catalogue_normalizes_meeting_race_and_entries() -> None:
    catalogue = parse_betfair_catalogue(
        envelope(
            {
                "jsonrpc": "2.0",
                "result": [
                    {
                        "marketId": "1.234",
                        "marketName": "R3 1200m Maiden",
                        "marketStartTime": "2026-10-12T04:30:00.000Z",
                        "event": {"id": "event-7", "name": "Randwick"},
                        "runners": [
                            {"selectionId": 11, "runnerName": "Alpha", "sortPriority": 2},
                            {"selectionId": 7, "runnerName": "Bravo", "sortPriority": 1},
                        ],
                    }
                ],
            }
        )
    )
    race = catalogue.races[0]
    assert race.race_id == "betfair:market:1.234"
    assert race.meeting_id == "betfair:event:event-7"
    assert race.race_number == 3
    assert [runner.number for runner in race.runners] == [1, 2]
    assert [runner.selection_id for runner in race.runners] == ["7", "11"]


def test_betfair_catalogue_rejects_missing_identity_and_duplicate_selection() -> None:
    with pytest.raises(BetfairCatalogueParseError, match="race number"):
        parse_betfair_catalogue(envelope({"result": [{"marketId": "1", "marketStartTime": "2026-10-12T00:00:00Z", "event": {"name": "Randwick"}, "marketName": "Maiden", "runners": [{"selectionId": 1, "runnerName": "A"}]}]}))
    with pytest.raises(BetfairCatalogueParseError, match="repeats selection"):
        parse_betfair_catalogue(envelope({"result": [{"marketId": "1", "marketStartTime": "2026-10-12T00:00:00Z", "event": {"name": "Randwick"}, "marketName": "R1 Maiden", "runners": [{"selectionId": 1, "runnerName": "A"}, {"selectionId": 1, "runnerName": "B"}]}]}))
