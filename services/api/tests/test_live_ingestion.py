from datetime import datetime, timezone

import pytest

from app.live_ingestion import persist_approved_live_envelope
from app.provenance import RawEnvelope, payload_sha256


class FakeResult:
    rowcount = 1

    def scalar_one(self):
        return "same-checksum"


class FakeConnection:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def execute(self, statement, params=None):
        self.calls.append((str(statement), params))
        return FakeResult()


def envelope(*, data_mode="LICENSED", rights_state="APPROVED"):
    payload = {"result": [{"marketId": "1.1"}]}
    now = datetime(2026, 10, 12, tzinfo=timezone.utc)
    return RawEnvelope(
        envelope_id="live-1",
        source_identifier="betfair-exchange:GET_MARKETS",
        payload=payload,
        payload_sha256=payload_sha256(payload),
        schema_version="provider-response-v1",
        retrieved_at=now,
        first_observed_at=now,
        data_mode=data_mode,
        rights_state=rights_state,
        licence_reference="owner-record:rights",
    )


def test_live_envelope_persists_receipt_before_raw_envelope() -> None:
    connection = FakeConnection()
    result = persist_approved_live_envelope(connection, envelope())
    assert result["disposition"] == "PERSISTED"
    assert result["source_receipt_id"] == "receipt:live-1"
    assert len(connection.calls) == 2
    assert "source_receipts" in connection.calls[0][0]
    assert "raw_envelopes" in connection.calls[1][0]


def test_unapproved_live_envelope_cannot_cross_persistence_boundary() -> None:
    with pytest.raises(ValueError, match="licensed, approved"):
        persist_approved_live_envelope(FakeConnection(), envelope(rights_state="UNASSESSED"))
