from datetime import datetime, timezone

import pytest

from app.live_projection import LiveProjectionError, parse_live_envelope
from app.provenance import RawEnvelope, payload_sha256


def envelope(payload):
    now = datetime(2026, 10, 12, tzinfo=timezone.utc)
    return RawEnvelope(
        envelope_id="provider-1",
        source_identifier="punters-edge:GET_RESULTS",
        payload=payload,
        payload_sha256=payload_sha256(payload),
        schema_version="provider-response-v1",
        retrieved_at=now,
        first_observed_at=now,
        data_mode="LICENSED",
        rights_state="APPROVED",
        licence_reference="owner-record:private-live-read",
    )


def test_provider_results_project_to_canonical_identity() -> None:
    races = parse_live_envelope(
        envelope(
            {
                "results": [
                    {
                        "raceId": "race-77",
                        "meeting": {"id": "meeting-7", "name": "Randwick"},
                        "startTime": "2026-10-12T04:30:00Z",
                        "raceNumber": 3,
                        "runners": [
                            {"runnerId": "horse-1", "horseName": "Alpha", "number": 1, "position": 1},
                            {"runnerId": "horse-2", "horseName": "Bravo", "number": 2, "position": 2},
                        ],
                    }
                ]
            }
        )
    )
    assert races[0].race_id == "punters-edge:race:race-77"
    assert races[0].meeting_id == "punters-edge:meeting:meeting-7"
    assert races[0].official is True
    assert [runner.position for runner in races[0].runners] == [1, 2]


def test_provider_projection_rejects_ambiguous_payload() -> None:
    with pytest.raises(LiveProjectionError, match="no supported race collection"):
        parse_live_envelope(envelope({"message": "not a racing response"}))


