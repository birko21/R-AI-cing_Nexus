from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.market import ingest_market_quote
from app.market_history import MarketHistory, MarketHistoryPolicy


BASE = datetime(2026, 1, 15, 10, tzinfo=timezone.utc)


def quote(quote_id: str, source: datetime, retrieved: datetime, **overrides: object):
    raw = {
        "quote_id": quote_id,
        "mapping": {
            "mapping_id": "map-1", "code": "THOROUGHBRED", "race_id": "THOROUGHBRED:fixture:race-1",
            "field_revision": "field-r1", "entry_id": "THOROUGHBRED:fixture:entry-1", "market_source": "fixture",
            "market_id": "market-1", "selection_id": "selection-1",
        },
        "market_type": "WIN", "price_type": "DECIMAL", "price": 3.5,
        "source_timestamp": source, "retrieved_at": retrieved, "in_play": False,
        "entitlement_reference": "synthetic-fixture", "source_receipt_id": "receipt-1",
        "data_mode": "SYNTHETIC_ONLY", "rights_state": "SYNTHETIC",
    }
    raw.update(overrides)
    result = ingest_market_quote(raw)
    assert result.quote is not None
    return result.quote


def test_as_of_uses_only_quotes_available_before_cutoff_and_never_uses_later_closing_quote() -> None:
    history = MarketHistory()
    history.append(quote("live", BASE, BASE + timedelta(minutes=1)))
    history.append(quote("closing", BASE + timedelta(hours=2), BASE + timedelta(hours=2), price_phase="CLOSING", price=2.0))

    before_close = history.as_of("map-1", BASE + timedelta(minutes=30))
    after_close = history.as_of("map-1", BASE + timedelta(hours=3))

    assert before_close.quote is not None and before_close.quote.quote_id == "live"
    assert before_close.availability == "AVAILABLE"
    assert after_close.quote is not None and after_close.quote.quote_id == "closing"
    assert after_close.availability == "CLOSING"


def test_as_of_distinguishes_delayed_stale_and_missing() -> None:
    history = MarketHistory(MarketHistoryPolicy(delayed_after=timedelta(minutes=5), stale_after=timedelta(hours=1)))
    history.append(quote("delayed", BASE - timedelta(minutes=10), BASE))
    delayed = history.as_of("map-1", BASE)
    assert delayed.availability == "DELAYED"

    stale_history = MarketHistory()
    stale_history.append(quote("stale", BASE - timedelta(hours=2), BASE - timedelta(hours=1, minutes=30)))
    assert stale_history.as_of("map-1", BASE).availability == "STALE"
    assert MarketHistory().as_of("map-1", BASE).availability == "MISSING"


def test_future_source_timestamp_is_not_admitted_into_as_of_history() -> None:
    history = MarketHistory()
    history.append(quote("future", BASE + timedelta(hours=1), BASE + timedelta(hours=1)))

    result = history.as_of("map-1", BASE)

    assert result.availability == "MISSING"


def test_history_is_append_only_and_cutoff_requires_timezone() -> None:
    history = MarketHistory()
    item = quote("one", BASE, BASE)
    history.append(item)
    with pytest.raises(ValueError, match="append-only"):
        history.append(item)
    with pytest.raises(ValueError, match="timezone"):
        history.as_of("map-1", datetime(2026, 1, 15, 10))
