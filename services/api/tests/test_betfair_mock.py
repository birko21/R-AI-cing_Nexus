from datetime import timedelta

import pytest

from app.betfair_mock import (
    BETFAIR_SYNTHETIC_RETRIEVED_AT,
    SyntheticBetfairExchangeAdapter,
    SyntheticBetfairMarket,
    SyntheticBetfairRunner,
    synthetic_betfair_markets,
)
from app.market_history import MarketHistory
from app.providers import AdapterContractError, ContractedProviderAdapter


def test_synthetic_betfair_fixture_is_read_only_and_contract_compatible() -> None:
    adapter = ContractedProviderAdapter(SyntheticBetfairExchangeAdapter())

    assert adapter.capabilities.provider_id == "betfair-exchange-synthetic"
    assert adapter.capabilities.data_mode == "SYNTHETIC_ONLY"
    assert adapter.capabilities.rights_state == "SYNTHETIC"
    assert adapter.capabilities.supported_operations == frozenset({"GET_MARKETS"})
    assert "available_back_volume" in adapter.capabilities.supported_fields
    assert "starting_price_post_race" in adapter.capabilities.supported_fields
    assert all(record.retrieval_metadata["credentials_used"] is False for record in adapter.fetch("GET_MARKETS", code="THOROUGHBRED").records)

    with pytest.raises(AdapterContractError, match="does not support operation"):
        adapter.fetch("GET_RESULTS", code="THOROUGHBRED")


def test_synthetic_betfair_exposes_catalogue_runner_book_history_and_sp() -> None:
    adapter = SyntheticBetfairExchangeAdapter()
    market = synthetic_betfair_markets()[0]
    page = ContractedProviderAdapter(adapter).fetch("GET_MARKETS", code=market.code)
    payload = page.records[0].payload

    catalogue = payload["market_catalogue"]
    book = payload["market_book"]
    assert catalogue["market_id"] == market.market_id
    assert len(catalogue["runners"]) == 3
    assert book["read_only"] is True
    assert book["runners"][0]["available_to_back"][0]["size"] > 0
    assert book["runners"][0]["matched_volume"] > 0
    assert book["runners"][0]["starting_price_status"] == "POST_RACE_SYNTHETIC_ONLY"
    assert len(payload["historical_price_observations"][0]["observations"]) == 2

    quotes = adapter.market_quotes(market.market_id)
    assert len(quotes) == len(market.runners)
    assert all(quote.data_mode == "SYNTHETIC_ONLY" for quote in quotes)
    assert all(quote.source_timestamp <= quote.retrieved_at for quote in quotes)
    assert all(quote.size is not None and quote.liquidity is not None for quote in quotes)

    history = MarketHistory()
    for quote in quotes:
        history.append(quote)
    snapshot = history.as_of(quotes[0].mapping.mapping_id, BETFAIR_SYNTHETIC_RETRIEVED_AT)
    assert snapshot.availability == "DELAYED"


def test_synthetic_betfair_supports_all_three_local_racing_codes() -> None:
    adapter = ContractedProviderAdapter(SyntheticBetfairExchangeAdapter())
    for code in ("THOROUGHBRED", "HARNESS", "GREYHOUND"):
        page = adapter.fetch("GET_MARKETS", code=code)
        assert len(page.records) == 1
        assert page.records[0].payload["market_catalogue"]["code"] == code


def test_synthetic_betfair_rejects_future_source_points_and_duplicate_runner_ids() -> None:
    future_market = synthetic_betfair_markets()[0]
    future_runner = SyntheticBetfairRunner(
        selection_id="future-selection", entry_id="future-entry", runner_name="Future", status="ACTIVE",
        price_history=(future_market.runners[0].price_history[-1].__class__(
            source_timestamp=BETFAIR_SYNTHETIC_RETRIEVED_AT + timedelta(minutes=1), back_price=2.0, lay_price=2.1,
            available_back_volume=1.0, available_lay_volume=1.0, matched_volume=1.0,
        ),), starting_price=None,
    )
    with pytest.raises(ValueError, match="source timestamps"):
        SyntheticBetfairExchangeAdapter((SyntheticBetfairMarket(
            future_market.market_id, future_market.code, future_market.race_id, future_market.field_revision,
            future_market.market_name, future_market.venue, future_market.market_start_time, (future_runner,)
        ),))

    duplicate = future_market.runners[0]
    with pytest.raises(ValueError, match="identities must be unique"):
        SyntheticBetfairMarket(
            future_market.market_id, future_market.code, future_market.race_id, future_market.field_revision,
            future_market.market_name, future_market.venue, future_market.market_start_time, (duplicate, duplicate)
        )
