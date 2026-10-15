from datetime import datetime, timezone

import pytest

from app.betfair_live_projection import parse_betfair_catalogue
from app.betfair_market_book import BetfairBookParseError, normalise_betfair_market_book, parse_betfair_market_book
from app.provenance import RawEnvelope, payload_sha256


NOW = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)


def envelope(payload: dict[str, object]) -> RawEnvelope:
    return RawEnvelope(
        envelope_id="receipt-book-1",
        source_identifier="betfair-exchange:GET_MARKETS",
        payload=payload,
        payload_sha256=payload_sha256(payload),
        schema_version="provider-response-v1",
        retrieved_at=NOW,
        first_observed_at=NOW,
        published_at=None,
        data_mode="LICENSED",
        rights_state="APPROVED",
        licence_reference="betfair-owner-approved",
        retrieval_metadata={"view": "book"},
    )


def catalogue_envelope() -> RawEnvelope:
    return envelope({
        "result": [{
            "marketId": "1.234",
            "marketStartTime": "2026-10-17T04:15:00Z",
            "event": {"id": "event-1", "name": "Randwick"},
            "marketName": "R7 TAB Everest",
            "runners": [
                {"selectionId": 101, "runnerName": "Runner One", "metadata": {"CLOTH_NUMBER": "1"}},
                {"selectionId": 102, "runnerName": "Runner Two", "metadata": {"CLOTH_NUMBER": "2"}},
            ],
        }]
    })


def book_envelope() -> RawEnvelope:
    return envelope({
        "result": [{
            "marketId": "1.234",
            "status": "OPEN",
            "publishTime": "2026-10-16T11:59:00Z",
            "inPlay": False,
            "totalMatched": 12500.0,
            "runners": [
                {
                    "selectionId": 101,
                    "status": "ACTIVE",
                    "totalMatched": 7000.0,
                    "ex": {
                        "availableToBack": [{"price": 3.2, "size": 100.0}, {"price": 3.1, "size": 200.0}],
                        "availableToLay": [{"price": 3.3, "size": 80.0}],
                        "tradedVolume": [[3.2, 500.0]],
                    },
                },
                {
                    "selectionId": 102,
                    "status": "REMOVED",
                    "ex": {"availableToBack": [], "availableToLay": []},
                },
            ],
        }]
    })


def test_market_book_parses_timestamped_prices_and_liquidity() -> None:
    books = parse_betfair_market_book(book_envelope())
    assert len(books) == 1
    assert books[0].source_timestamp.isoformat() == "2026-10-16T11:59:00+00:00"
    assert books[0].runners[0].available_to_back[0].price == 3.2
    assert books[0].total_matched == 12500


def test_market_book_normalises_only_exact_catalogue_selections() -> None:
    normalised = normalise_betfair_market_book(book_envelope(), parse_betfair_catalogue(catalogue_envelope()))
    assert len(normalised.quotes) == 2
    assert {quote.mapping.selection_id for quote in normalised.quotes} == {"101"}
    assert {quote.price for quote in normalised.quotes} == {3.2, 3.3}
    assert all(quote.mapping.entry_id.startswith("betfair:market:1.234") for quote in normalised.quotes)


def test_market_book_rejects_missing_publish_time_instead_of_inventing_one() -> None:
    payload = book_envelope().model_copy(update={"payload": {"result": [{"marketId": "1.234", "status": "OPEN", "runners": []}]}})
    with pytest.raises(BetfairBookParseError, match="publishTime"):
        parse_betfair_market_book(payload)


def test_market_book_rejects_post_retrieval_publish_time() -> None:
    payload = book_envelope().model_copy(update={
        "payload": {
            **book_envelope().payload,
            "result": [{**book_envelope().payload["result"][0], "publishTime": "2026-10-16T12:01:00Z"}],
        }
    })
    with pytest.raises(BetfairBookParseError, match="later than retrieval"):
        parse_betfair_market_book(payload)
