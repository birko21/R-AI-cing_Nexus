from __future__ import annotations

from datetime import timedelta

import pytest

from app.market import ingest_market_quote
from app.market_math import ComparabilityPolicy, MarketMathError, compare_market_quotes, implied_probability
from app.testsupport import quote_fixture


def quote(quote_id: str, selection_id: str, **overrides: object):
    raw = quote_fixture(quote_id, selection_id, **overrides)
    result = ingest_market_quote(raw)
    assert result.quote is not None
    return result.quote


def test_declared_price_types_convert_to_reference_implied_probabilities() -> None:
    assert implied_probability("DECIMAL", 4.0) == pytest.approx(0.25)
    assert implied_probability("FRACTIONAL", 3.0) == pytest.approx(0.25)
    assert implied_probability("AMERICAN", 300) == pytest.approx(0.25)
    assert implied_probability("AMERICAN", -300) == pytest.approx(0.75)


def test_comparison_returns_overround_and_margin_normalized_probabilities() -> None:
    result = compare_market_quotes([quote("q1", "selection-1", price=2.0), quote("q2", "selection-2", price=4.0)])

    assert result.status == "COMPARABLE"
    assert result.overround == pytest.approx(0.75)
    assert sum(result.normalized_probabilities.values()) == pytest.approx(1.0)
    assert result.normalized_probabilities["selection-1"] == pytest.approx(2 / 3)


@pytest.mark.parametrize(
    "quotes,reason",
    [
        ([None, "q2"], "missing"),
        (["q1", "q1"], "duplicate"),
    ],
)
def test_incomplete_or_duplicate_inputs_are_not_comparable(quotes: list[object], reason: str) -> None:
    actual = [None if item is None else quote(item, "selection-1" if item == "q1" else "selection-2") for item in quotes]
    result = compare_market_quotes(actual)
    assert result.status == "NOT_COMPARABLE"
    assert reason in result.reason


def test_scratched_runner_is_excluded_and_one_remaining_runner_is_not_comparable() -> None:
    result = compare_market_quotes([
        quote("q1", "selection-1", runner_status="SCRATCHED"),
        quote("q2", "selection-2"),
    ])
    assert result.status == "NOT_COMPARABLE"
    assert "active runners" in result.reason


def test_mismatched_timestamps_and_invalid_odds_are_not_comparable() -> None:
    timestamps = compare_market_quotes([
        quote("q1", "selection-1"),
        quote(
            "q2", "selection-2",
            source_timestamp=quote_fixture("q2", "selection-2")["source_timestamp"] + timedelta(minutes=6),
            retrieved_at=quote_fixture("q2", "selection-2")["retrieved_at"] + timedelta(minutes=6),
        ),
    ], ComparabilityPolicy(max_timestamp_skew=timedelta(minutes=5)))
    invalid = ingest_market_quote(quote_fixture("q1", "selection-1", price=0.5))

    assert timestamps.status == "NOT_COMPARABLE"
    assert "timestamps" in timestamps.reason
    assert invalid.quarantine is not None
    assert invalid.quarantine.reason_code == "INVALID_QUOTE"


def test_invalid_reference_math_is_explicit() -> None:
    with pytest.raises(MarketMathError):
        implied_probability("DECIMAL", 0.5)
