from __future__ import annotations

from datetime import datetime, timezone

from app.market import ingest_market_quote


NOW = datetime(2026, 1, 15, 10, tzinfo=timezone.utc)


def raw_quote(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "quote_id": "quote-1",
        "mapping": {
            "mapping_id": "map-1", "code": "THOROUGHBRED", "race_id": "THOROUGHBRED:fixture:race-1",
            "field_revision": "field-r1", "entry_id": "THOROUGHBRED:fixture:entry-1", "market_source": "fixture",
            "market_id": "market-1", "selection_id": "selection-1",
        },
        "market_type": "WIN", "price_type": "DECIMAL", "price": 3.5,
        "source_timestamp": NOW, "retrieved_at": NOW, "in_play": False,
        "size": 100.0, "liquidity": 1000.0, "entitlement_reference": "synthetic-fixture",
        "source_receipt_id": "receipt-1", "data_mode": "SYNTHETIC_ONLY", "rights_state": "SYNTHETIC",
    }
    value.update(overrides)
    return value


def test_quote_binds_exact_runner_and_field_revision_with_provenance() -> None:
    result = ingest_market_quote(raw_quote())

    assert result.quarantine is None
    assert result.quote is not None
    assert result.quote.mapping.entry_id == "THOROUGHBRED:fixture:entry-1"
    assert result.quote.mapping.field_revision == "field-r1"
    assert result.quote.price_type == "DECIMAL"
    assert result.quote.in_play is False
    assert result.quote.size == 100.0
    assert result.quote.liquidity == 1000.0
    assert result.quote.entitlement_reference == "synthetic-fixture"


def test_name_only_or_incomplete_mapping_is_quarantined() -> None:
    raw = raw_quote(mapping={"runner_name": "Unnamed runner", "market_id": "market-1"})

    result = ingest_market_quote(raw)

    assert result.quote is None
    assert result.quarantine is not None
    assert result.quarantine.reason_code == "MISSING_EXACT_MAPPING"


def test_quote_rejects_invalid_price_and_source_ordering() -> None:
    invalid_price = ingest_market_quote(raw_quote(price=0.5))
    future_source = ingest_market_quote(raw_quote(source_timestamp=datetime(2026, 1, 15, 11, tzinfo=timezone.utc)))

    assert invalid_price.quarantine is not None
    assert invalid_price.quarantine.reason_code == "INVALID_QUOTE"
    assert future_source.quarantine is not None
    assert future_source.quarantine.reason_code == "INVALID_QUOTE"


def test_quote_rejects_unapproved_license_mode() -> None:
    result = ingest_market_quote(raw_quote(data_mode="LICENSED", rights_state="UNASSESSED"))

    assert result.quarantine is not None
    assert result.quarantine.reason_code == "INVALID_QUOTE"


def test_quote_supports_in_play_and_price_metadata_without_order_operations() -> None:
    result = ingest_market_quote(raw_quote(price_type="AMERICAN", price=-120, in_play=True, size=None, liquidity=None))

    assert result.quarantine is None
    assert result.quote is not None
    assert result.quote.in_play is True
