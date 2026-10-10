from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

import pytest

from app.provenance import RawEnvelope, payload_sha256
from app.scraped_provenance import ReplayFixture, ScrapedProvenanceError, ScrapedProvenanceStore, ScrapedSourceReceipt


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)
PAYLOAD = {"race": "PUBLIC:fixture:race-1", "status": "OFFICIAL"}


def fixture() -> ReplayFixture:
    return ReplayFixture.from_payload("replay-1", PAYLOAD, "parser-v1")


def receipt(**overrides: object) -> ScrapedSourceReceipt:
    values: dict[str, object] = {
        "receipt_id": "receipt-1",
        "envelope": RawEnvelope(
            envelope_id="env-1",
            source_identifier="https://public.example/racing/race-1",
            payload=PAYLOAD,
            payload_sha256=payload_sha256(PAYLOAD),
            schema_version="scraped-race-v1",
            retrieved_at=NOW,
            first_observed_at=NOW,
            data_mode="SCRAPED_PUBLIC",
            rights_state="UNASSESSED",
            retrieval_metadata={"parser_version": "parser-v1", "fixture_id": "replay-1"},
        ),
        "retrieval_url": "https://public.example/racing/race-1",
        "retrieved_at": NOW,
        "content_sha256": fixture().content_sha256,
        "parser_version": "parser-v1",
        "replay_fixture_id": "replay-1",
        "retention_until": datetime(2026, 2, 1, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return ScrapedSourceReceipt(**values)


def parse_json(content: bytes) -> dict[str, object]:
    return json.loads(content.decode("utf-8"))


def test_provenance_view_preserves_scraped_identity_and_default_non_official_status() -> None:
    store = ScrapedProvenanceStore()
    store.append(receipt(), fixture())

    view = store.provenance_view("receipt-1", NOW)

    assert view["retrieval_url"] == "https://public.example/racing/race-1"
    assert view["content_sha256"] == fixture().content_sha256
    assert view["parser_version"] == "parser-v1"
    assert view["data_mode"] == "SCRAPED_PUBLIC"
    assert view["rights_state"] == "UNASSESSED"
    assert view["retention_status"] == "ACTIVE"
    assert view["licensed"] is False
    assert view["official"] is False


def test_replay_fixture_reproduces_the_stored_payload_and_hash() -> None:
    store = ScrapedProvenanceStore()
    store.append(receipt(), fixture())

    assert store.replay("receipt-1", parse_json, NOW) == PAYLOAD


def test_expired_retention_blocks_replay_but_keeps_provenance_visible() -> None:
    store = ScrapedProvenanceStore()
    store.append(receipt(), fixture())
    expired = datetime(2026, 2, 1, tzinfo=timezone.utc)

    assert store.provenance_view("receipt-1", expired)["retention_status"] == "EXPIRED"
    with pytest.raises(ScrapedProvenanceError, match="retention expiry"):
        store.replay("receipt-1", parse_json, expired)


def test_receipts_and_fixtures_are_append_only_and_hash_bound() -> None:
    store = ScrapedProvenanceStore()
    store.append(receipt(), fixture())
    with pytest.raises(ScrapedProvenanceError, match="append-only"):
        store.append(receipt(), fixture())

    with pytest.raises(ScrapedProvenanceError, match="checksum"):
        ReplayFixture("replay-bad", "{}", hashlib.sha256(b"different").hexdigest(), "parser-v1")


@pytest.mark.parametrize(
    "overrides",
    [
        {"retrieval_url": "http://public.example/racing/race-1"},
        {"envelope": RawEnvelope(
            envelope_id="env-2", source_identifier="https://public.example/racing/race-2", payload=PAYLOAD,
            payload_sha256=payload_sha256(PAYLOAD), schema_version="scraped-race-v1", retrieved_at=NOW,
            first_observed_at=NOW, data_mode="SYNTHETIC_ONLY", rights_state="SYNTHETIC",
        )},
    ],
)
def test_scraped_receipt_rejects_invalid_mode_or_url(overrides: dict[str, object]) -> None:
    with pytest.raises(ScrapedProvenanceError):
        receipt(**overrides)
