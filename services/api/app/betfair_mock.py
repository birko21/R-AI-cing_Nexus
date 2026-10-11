"""Synthetic, read-only Betfair market intelligence for offline development.

This module deliberately models the shape of Betfair market intelligence without
contacting Betfair.  It is an executable contract fixture for catalogue identity,
runner identity, pre-race prices, available volume, matched liquidity, historical
price observations and starting-price observations.  The starting-price field is
labelled as post-race information by the payload contract and must not enter a
pre-race feature snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from app.domain import MarketSelectionMapping, VALID_CODES
from app.market import MarketQuote
from app.provenance import RawEnvelope, payload_sha256
from app.providers import (
    AdapterPage,
    PaginationCapability,
    ProviderCapabilities,
    ProviderOperation,
    QuotaCapability,
)


BETFAIR_SYNTHETIC_PROVIDER_ID = "betfair-exchange-synthetic"
BETFAIR_SYNTHETIC_SCHEMA_VERSION = "betfair-market-fixture-v1"
BETFAIR_SYNTHETIC_RETRIEVED_AT = datetime(2026, 1, 15, 1, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class SyntheticBetfairPricePoint:
    source_timestamp: datetime
    back_price: float
    lay_price: float
    available_back_volume: float
    available_lay_volume: float
    matched_volume: float

    def __post_init__(self) -> None:
        if self.source_timestamp.tzinfo is None or self.source_timestamp.utcoffset() is None:
            raise ValueError("synthetic Betfair price timestamps must be timezone-aware")
        if self.back_price < 1 or self.lay_price < 1:
            raise ValueError("synthetic Betfair prices must be decimal odds >= 1")
        if min(self.available_back_volume, self.available_lay_volume, self.matched_volume) < 0:
            raise ValueError("synthetic Betfair volumes cannot be negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "source_timestamp": self.source_timestamp.isoformat().replace("+00:00", "Z"),
            "back_price": self.back_price,
            "lay_price": self.lay_price,
            "available_back_volume": self.available_back_volume,
            "available_lay_volume": self.available_lay_volume,
            "matched_volume": self.matched_volume,
        }


@dataclass(frozen=True)
class SyntheticBetfairRunner:
    selection_id: str
    entry_id: str
    runner_name: str
    status: Literal["ACTIVE", "REMOVED"]
    price_history: tuple[SyntheticBetfairPricePoint, ...]
    starting_price: float | None

    def to_catalogue_dict(self) -> dict[str, object]:
        return {
            "selection_id": self.selection_id,
            "entry_id": self.entry_id,
            "runner_name": self.runner_name,
            "status": self.status,
        }

    def latest_price(self) -> SyntheticBetfairPricePoint:
        if not self.price_history:
            raise ValueError("synthetic Betfair runner requires price history")
        return self.price_history[-1]

    def to_book_dict(self) -> dict[str, object]:
        latest = self.latest_price()
        return {
            "selection_id": self.selection_id,
            "status": self.status,
            "available_to_back": [{"price": latest.back_price, "size": latest.available_back_volume}],
            "available_to_lay": [{"price": latest.lay_price, "size": latest.available_lay_volume}],
            "matched_volume": latest.matched_volume,
            "starting_price": self.starting_price,
            "starting_price_status": "POST_RACE_SYNTHETIC_ONLY" if self.starting_price is not None else "NOT_AVAILABLE",
        }


@dataclass(frozen=True)
class SyntheticBetfairMarket:
    market_id: str
    code: str
    race_id: str
    field_revision: str
    market_name: str
    venue: str
    market_start_time: datetime
    runners: tuple[SyntheticBetfairRunner, ...]

    def __post_init__(self) -> None:
        if self.code not in VALID_CODES:
            raise ValueError("synthetic Betfair market uses an unsupported racing code")
        if self.market_start_time.tzinfo is None or self.market_start_time.utcoffset() is None:
            raise ValueError("synthetic Betfair market start time must be timezone-aware")
        selection_ids = [runner.selection_id for runner in self.runners]
        entry_ids = [runner.entry_id for runner in self.runners]
        if not self.runners or len(selection_ids) != len(set(selection_ids)) or len(entry_ids) != len(set(entry_ids)):
            raise ValueError("synthetic Betfair market runner identities must be unique")

    def to_payload(self) -> dict[str, object]:
        return {
            "provider": "BETFAIR_EXCHANGE",
            "market_catalogue": {
                "market_id": self.market_id,
                "market_name": self.market_name,
                "venue": self.venue,
                "code": self.code,
                "race_id": self.race_id,
                "field_revision": self.field_revision,
                "market_start_time": self.market_start_time.isoformat().replace("+00:00", "Z"),
                "runners": [runner.to_catalogue_dict() for runner in self.runners],
            },
            "market_book": {
                "market_id": self.market_id,
                "read_only": True,
                "runners": [runner.to_book_dict() for runner in self.runners],
            },
            "historical_price_observations": [
                {
                    "selection_id": runner.selection_id,
                    "observations": [point.to_dict() for point in runner.price_history],
                }
                for runner in self.runners
            ],
            "starting_price_scope": "synthetic_post_race_observation_only",
        }


def _price_history(start: datetime, back: float, lay: float, matched: float) -> tuple[SyntheticBetfairPricePoint, ...]:
    return (
        SyntheticBetfairPricePoint(start - timedelta(minutes=20), back + 0.4, lay + 0.5, 40.0, 35.0, matched / 2),
        SyntheticBetfairPricePoint(start - timedelta(minutes=5), back, lay, 55.0, 48.0, matched),
    )


def synthetic_betfair_markets() -> tuple[SyntheticBetfairMarket, ...]:
    """Return deterministic three-code fixture data with no external dependency."""

    start = datetime(2026, 1, 15, 1, 0, tzinfo=timezone.utc)
    definitions = (
        ("THOROUGHBRED", "bf.au.tb.1001", "RIL-Synthetic-1", "Rosehill", "R1 Synthetic Sprint", ("Atlas", "Beryl", "Comet")),
        ("HARNESS", "bf.au.h.1002", "RIL-Synthetic-2", "Menangle", "R2 Synthetic Pace", ("Driver One", "Driver Two", "Driver Three")),
        ("GREYHOUND", "bf.au.g.1003", "RIL-Synthetic-3", "Wentworth Park", "R3 Synthetic Grade", ("Rapid", "Shadow", "Vector")),
    )
    markets: list[SyntheticBetfairMarket] = []
    for index, (code, market_id, field_revision, venue, market_name, names) in enumerate(definitions):
        runners = tuple(
            SyntheticBetfairRunner(
                selection_id=f"{market_id}:{runner_number}",
                entry_id=f"{code}:SYNTHETIC:{index + 1}:{runner_number}",
                runner_name=name,
                status="ACTIVE",
                price_history=_price_history(start, 2.0 + runner_number * 0.7, 2.1 + runner_number * 0.7, 100.0 + runner_number * 25),
                starting_price=2.3 + runner_number * 0.8,
            )
            for runner_number, name in enumerate(names, start=1)
        )
        markets.append(SyntheticBetfairMarket(market_id, code, f"race:{index + 1}", field_revision, market_name, venue, start, runners))
    return tuple(markets)


def _parse_cursor(cursor: str | None) -> int:
    if cursor is None:
        return 0
    if not cursor.startswith("offset:"):
        raise ValueError("synthetic Betfair cursor is invalid")
    try:
        offset = int(cursor.removeprefix("offset:"))
    except ValueError as exc:
        raise ValueError("synthetic Betfair cursor is invalid") from exc
    if offset < 0:
        raise ValueError("synthetic Betfair cursor is invalid")
    return offset


class SyntheticBetfairExchangeAdapter:
    """Contract adapter for offline Betfair-shaped market intelligence only."""

    def __init__(self, markets: tuple[SyntheticBetfairMarket, ...] | None = None) -> None:
        self._markets = markets or synthetic_betfair_markets()
        for market in self._markets:
            for runner in market.runners:
                if any(point.source_timestamp > BETFAIR_SYNTHETIC_RETRIEVED_AT for point in runner.price_history):
                    raise ValueError("synthetic Betfair source timestamps cannot be after retrieval")
        self.capabilities = ProviderCapabilities(
            provider_id=BETFAIR_SYNTHETIC_PROVIDER_ID,
            display_name="Betfair Exchange (synthetic fixture)",
            supported_codes=frozenset(VALID_CODES),
            supported_fields=frozenset({
                "market_catalogue", "market_id", "market_start_time", "runner_selection_id", "runner_name",
                "pre_race_back_price", "pre_race_lay_price", "historical_odds", "available_back_volume",
                "available_lay_volume", "matched_volume", "starting_price_post_race",
            }),
            timestamp_fields=frozenset({"retrieved_at", "first_observed_at", "published_at"}),
            data_mode="SYNTHETIC_ONLY",
            rights_state="SYNTHETIC",
            pagination=PaginationCapability(True, "CURSOR", 100),
            quotas=QuotaCapability(unknown=True, notes="Fixture has no external quota or cost."),
            supported_operations=frozenset({"GET_MARKETS"}),
            unsupported_operations=frozenset({"LIST_MEETINGS", "GET_RACES", "GET_ENTRIES", "GET_RESULTS"}),
            enabled=True,
        )

    @property
    def markets(self) -> tuple[SyntheticBetfairMarket, ...]:
        return self._markets

    def fetch(self, operation: ProviderOperation, *, code: str, cursor: str | None = None, page_size: int | None = None) -> AdapterPage:
        if operation != "GET_MARKETS":
            raise ValueError("synthetic Betfair adapter is read-only and only supports GET_MARKETS")
        if code not in self.capabilities.supported_codes:
            raise ValueError(f"synthetic Betfair adapter does not support racing code {code}")
        limit = page_size or 100
        if limit < 1 or limit > 100:
            raise ValueError("synthetic Betfair page_size must be between 1 and 100")
        offset = _parse_cursor(cursor)
        selected = tuple(market for market in self._markets if market.code == code)
        page = selected[offset : offset + limit]
        records = tuple(
            RawEnvelope(
                envelope_id=f"synthetic-betfair:{market.market_id}",
                source_identifier=f"betfair:market:{market.market_id}",
                payload=market.to_payload(),
                payload_sha256=payload_sha256(market.to_payload()),
                schema_version=BETFAIR_SYNTHETIC_SCHEMA_VERSION,
                retrieved_at=BETFAIR_SYNTHETIC_RETRIEVED_AT,
                first_observed_at=BETFAIR_SYNTHETIC_RETRIEVED_AT,
                published_at=None,
                data_mode="SYNTHETIC_ONLY",
                rights_state="SYNTHETIC",
                retrieval_metadata={"transport": "offline_fixture", "read_only": True, "credentials_used": False},
            )
            for market in page
        )
        next_cursor = f"offset:{offset + limit}" if offset + limit < len(selected) else None
        return AdapterPage(records=records, next_cursor=next_cursor, as_of=BETFAIR_SYNTHETIC_RETRIEVED_AT)

    def market_book(self, market_id: str) -> dict[str, object]:
        """Return a read-only synthetic market book; no order or staking operation exists."""

        for market in self._markets:
            if market.market_id == market_id:
                payload = market.to_payload()
                return payload["market_book"]  # type: ignore[return-value]
        raise KeyError(market_id)

    def market_quotes(self, market_id: str) -> tuple[MarketQuote, ...]:
        market = next((item for item in self._markets if item.market_id == market_id), None)
        if market is None:
            raise KeyError(market_id)
        quotes: list[MarketQuote] = []
        for runner in market.runners:
            point = runner.latest_price()
            mapping = MarketSelectionMapping(
                mapping_id=f"{market.market_id}:{runner.selection_id}", code=market.code, race_id=market.race_id,
                field_revision=market.field_revision, entry_id=runner.entry_id, market_source="BETFAIR_EXCHANGE",
                market_id=market.market_id, selection_id=runner.selection_id,
            )
            quotes.append(MarketQuote(
                quote_id=f"synthetic-betfair-quote:{market.market_id}:{runner.selection_id}", mapping=mapping,
                market_type="WIN", price_type="DECIMAL", price_phase="LIVE", runner_status=runner.status,
                price=point.back_price, source_timestamp=point.source_timestamp, retrieved_at=BETFAIR_SYNTHETIC_RETRIEVED_AT,
                in_play=False, size=point.available_back_volume, liquidity=point.matched_volume,
                entitlement_reference="synthetic-fixture", source_receipt_id=f"synthetic-betfair:{market.market_id}",
                data_mode="SYNTHETIC_ONLY", rights_state="SYNTHETIC",
            ))
        return tuple(quotes)


def build_synthetic_betfair_replay_manifest(
    adapter: SyntheticBetfairExchangeAdapter | None = None,
    *,
    page_size: int = 100,
) -> dict[str, object]:
    """Build deterministic page/checksum evidence for offline replay."""

    if page_size < 1 or page_size > 100:
        raise ValueError("synthetic Betfair replay page_size must be between 1 and 100")
    source = adapter or SyntheticBetfairExchangeAdapter()
    pages: list[dict[str, object]] = []
    for code in sorted(VALID_CODES):
        cursor: str | None = None
        page_number = 0
        while True:
            page = source.fetch("GET_MARKETS", code=code, cursor=cursor, page_size=page_size)
            pages.append(
                {
                    "code": code,
                    "page_number": page_number,
                    "cursor": cursor,
                    "next_cursor": page.next_cursor,
                    "as_of": page.as_of.isoformat().replace("+00:00", "Z") if page.as_of else None,
                    "envelopes": [
                        {
                            "envelope_id": record.envelope_id,
                            "source_identifier": record.source_identifier,
                            "payload_sha256": record.payload_sha256,
                            "schema_version": record.schema_version,
                        }
                        for record in page.records
                    ],
                }
            )
            page_number += 1
            cursor = page.next_cursor
            if cursor is None:
                break
    return {
        "schema_version": "betfair-market-replay-manifest-v1",
        "fixture_id": "ril-067-betfair-replay-v1",
        "provider_id": BETFAIR_SYNTHETIC_PROVIDER_ID,
        "page_size": page_size,
        "pages": pages,
        "record_count": sum(len(page["envelopes"]) for page in pages),
        "fictional": True,
        "data_mode": "SYNTHETIC_ONLY",
        "rights_state": "SYNTHETIC",
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Deterministic offline replay manifest; no external provider was contacted.",
    }
