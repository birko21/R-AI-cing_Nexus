"""Reference implied-probability math and conservative market comparability."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

from app.market import MarketQuote


ComparisonStatus = Literal["COMPARABLE", "NOT_COMPARABLE"]


class MarketMathError(ValueError):
    """Raised for an invalid declared odds representation."""


@dataclass(frozen=True)
class ComparabilityPolicy:
    max_timestamp_skew: timedelta = timedelta(minutes=5)

    def __post_init__(self) -> None:
        if self.max_timestamp_skew < timedelta(0):
            raise ValueError("timestamp skew cannot be negative")


@dataclass(frozen=True)
class MarketComparison:
    status: ComparisonStatus
    reason: str
    market_type: str | None
    overround: float | None
    implied_probabilities: dict[str, float]
    normalized_probabilities: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "market_type": self.market_type,
            "overround": self.overround,
            "implied_probabilities": self.implied_probabilities,
            "normalized_probabilities": self.normalized_probabilities,
        }


def implied_probability(price_type: str, price: float) -> float:
    if price_type == "DECIMAL":
        if price < 1:
            raise MarketMathError("decimal price must be at least 1")
        result = 1 / price
    elif price_type == "FRACTIONAL":
        if price <= 0:
            raise MarketMathError("fractional price must be positive")
        result = 1 / (price + 1)
    elif price_type == "AMERICAN":
        if price == 0:
            raise MarketMathError("american price cannot be zero")
        result = 100 / (price + 100) if price > 0 else abs(price) / (abs(price) + 100)
    else:
        raise MarketMathError(f"unsupported price type: {price_type}")
    if not 0 < result <= 1:
        raise MarketMathError("implied probability is outside (0, 1]")
    return result


def compare_market_quotes(quotes: Sequence[MarketQuote | None], policy: ComparabilityPolicy | None = None) -> MarketComparison:
    policy = policy or ComparabilityPolicy()
    if any(quote is None for quote in quotes):
        return MarketComparison("NOT_COMPARABLE", "one or more required quotes are missing", None, None, {}, {})
    active = [quote for quote in quotes if quote is not None and quote.runner_status == "ACTIVE"]
    if len(active) < 2:
        return MarketComparison("NOT_COMPARABLE", "fewer than two active runners remain", active[0].market_type if active else None, None, {}, {})
    market_keys = {
        (quote.mapping.code, quote.mapping.race_id, quote.mapping.field_revision, quote.mapping.market_id, quote.market_type)
        for quote in active
    }
    if len(market_keys) != 1:
        return MarketComparison("NOT_COMPARABLE", "quotes do not share an exact market and field revision", None, None, {}, {})
    selection_ids = [quote.mapping.selection_id for quote in active]
    if len(set(selection_ids)) != len(selection_ids):
        return MarketComparison("NOT_COMPARABLE", "duplicate market selections are present", active[0].market_type, None, {}, {})
    timestamps = [quote.source_timestamp for quote in active]
    if max(timestamps) - min(timestamps) > policy.max_timestamp_skew:
        return MarketComparison("NOT_COMPARABLE", "quote source timestamps exceed the comparability window", active[0].market_type, None, {}, {})
    try:
        implied = {quote.mapping.selection_id: implied_probability(quote.price_type, quote.price) for quote in active}
    except MarketMathError as exc:
        return MarketComparison("NOT_COMPARABLE", str(exc), active[0].market_type, None, {}, {})
    overround = sum(implied.values())
    if overround <= 0:
        return MarketComparison("NOT_COMPARABLE", "market overround is not positive", active[0].market_type, None, {}, {})
    normalized = {selection_id: probability / overround for selection_id, probability in implied.items()}
    return MarketComparison("COMPARABLE", "quotes share a market, field revision and timestamp window", active[0].market_type, overround, implied, normalized)
