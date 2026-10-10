"""Leakage-safe as-of reconstruction for timestamped market quotes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from app.market import MarketQuote


Availability = Literal["AVAILABLE", "DELAYED", "STALE", "MISSING", "CLOSING"]


@dataclass(frozen=True)
class MarketHistoryPolicy:
    delayed_after: timedelta = timedelta(minutes=5)
    stale_after: timedelta = timedelta(hours=1)

    def __post_init__(self) -> None:
        if self.delayed_after < timedelta(0) or self.stale_after <= timedelta(0):
            raise ValueError("market history thresholds are invalid")


@dataclass(frozen=True)
class QuoteSnapshot:
    mapping_id: str
    cutoff: datetime
    quote: MarketQuote | None
    availability: Availability
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "mapping_id": self.mapping_id,
            "cutoff": self.cutoff.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "quote_id": self.quote.quote_id if self.quote else None,
            "availability": self.availability,
            "reason": self.reason,
        }


class MarketHistory:
    """Append-only quote history with strict forecast-cutoff reconstruction."""

    def __init__(self, policy: MarketHistoryPolicy | None = None) -> None:
        self.policy = policy or MarketHistoryPolicy()
        self._quotes: dict[str, MarketQuote] = {}

    def append(self, quote: MarketQuote) -> None:
        if quote.quote_id in self._quotes:
            raise ValueError("market quote history is append-only")
        self._quotes[quote.quote_id] = quote

    def as_of(self, mapping_id: str, cutoff: datetime) -> QuoteSnapshot:
        if cutoff.tzinfo is None or cutoff.utcoffset() is None:
            raise ValueError("market cutoff must be timezone-aware")
        candidates = [
            quote for quote in self._quotes.values()
            if quote.mapping.mapping_id == mapping_id
            and quote.retrieved_at <= cutoff
            and quote.source_timestamp <= cutoff
        ]
        if not candidates:
            return QuoteSnapshot(mapping_id, cutoff, None, "MISSING", "no quote was available by the forecast cutoff")
        quote = max(candidates, key=lambda item: (item.retrieved_at, item.quote_id))
        age = cutoff - quote.source_timestamp
        if quote.price_phase == "CLOSING":
            return QuoteSnapshot(mapping_id, cutoff, quote, "CLOSING", "closing quote was available by the cutoff")
        if age >= self.policy.stale_after:
            return QuoteSnapshot(mapping_id, cutoff, quote, "STALE", "latest eligible quote exceeded the staleness threshold")
        if quote.retrieved_at - quote.source_timestamp >= self.policy.delayed_after:
            return QuoteSnapshot(mapping_id, cutoff, quote, "DELAYED", "quote was retrieved after its source timestamp")
        return QuoteSnapshot(mapping_id, cutoff, quote, "AVAILABLE", "latest eligible quote was available by the cutoff")
