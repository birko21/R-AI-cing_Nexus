from datetime import datetime, timezone

from app.provenance import ingest_raw_envelope, payload_sha256


def raw_envelope(**overrides):
    payload = {"race": "fictional-1", "value": 1}
    data = {
        "envelope_id": "env-1",
        "source_identifier": "synthetic://fixture/env-1",
        "payload": payload,
        "payload_sha256": payload_sha256(payload),
        "schema_version": "1.0",
        "retrieved_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "first_observed_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "data_mode": "SYNTHETIC_ONLY",
        "rights_state": "SYNTHETIC",
        "retrieval_metadata": {"fixture": True},
    }
    data.update(overrides)
    return data


def test_canonical_payload_checksum_is_accepted() -> None:
    result = ingest_raw_envelope(raw_envelope())
    assert result.quarantine is None
    assert result.envelope is not None
    assert result.envelope.data_mode == "SYNTHETIC_ONLY"


def test_checksum_mismatch_is_quarantined() -> None:
    result = ingest_raw_envelope(raw_envelope(payload_sha256="0" * 64))
    assert result.envelope is None
    assert result.quarantine is not None
    assert result.quarantine.reason_code == "CHECKSUM_MISMATCH"


def test_missing_source_and_missing_licence_are_quarantined() -> None:
    missing_source = ingest_raw_envelope(raw_envelope(source_identifier=""))
    assert missing_source.quarantine is not None
    assert missing_source.quarantine.reason_code == "MISSING_SOURCE_ID"

    missing_licence = ingest_raw_envelope(
        raw_envelope(
            data_mode="LICENSED",
            rights_state="APPROVED",
            licence_reference=None,
        )
    )
    assert missing_licence.quarantine is not None
    assert missing_licence.quarantine.reason_code == "RIGHTS_UNASSESSED"


def test_payload_ordering_does_not_change_checksum() -> None:
    assert payload_sha256({"a": 1, "b": 2}) == payload_sha256({"b": 2, "a": 1})
