"""Strict normalisation of Betfair read-only market-book observations.

The catalogue establishes exact race/selection identity.  This module turns a
subsequent ``listMarketBook`` response into immutable, pre-race quote records.
It intentionally ignores SP fields: starting price is a settlement
observation and must not leak into a pre-race feature snapshot.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Any

from sqlalchemy import Connection, text

from app.betfair_live_projection import BetfairCatalogue
from app.market import QuoteIngestResult, ingest_market_quote
from app.provenance import RawEnvelope


class BetfairBookParseError(ValueError):
    """Raised when a market book cannot be safely normalised."""


@dataclass(frozen=True)
class BetfairPriceLevel:
    price: float
    size: float


@dataclass(frozen=True)
class BetfairRunnerBook:
    selection_id: str
    status: str
    available_to_back: tuple[BetfairPriceLevel, ...]
    available_to_lay: tuple[BetfairPriceLevel, ...]
    traded_volume: tuple[BetfairPriceLevel, ...]
    last_price_traded: float | None
    total_matched: float | None


@dataclass(frozen=True)
class BetfairMarketBook:
    market_id: str
    status: str
    source_timestamp: datetime
    in_play: bool
    total_matched: float | None
    runners: tuple[BetfairRunnerBook, ...]


@dataclass(frozen=True)
class BetfairBookNormalisation:
    books: tuple[BetfairMarketBook, ...]
    quotes: tuple[object, ...]
    quarantines: tuple[object, ...]


def project_betfair_market_book(connection: Connection, envelope: RawEnvelope) -> dict[str, int]:
    """Persist a book capture after catalogue mappings have been projected."""

    books = parse_betfair_market_book(envelope)
    receipt_id = f"receipt:{envelope.envelope_id}"
    quotes = 0
    quarantines = 0
    for book in books:
        mappings = {
            str(row.selection_id): row
            for row in connection.execute(
                text(
                    """
                    SELECT mapping_id, code, race_id, field_revision, entry_id,
                           market_source, market_id, selection_id
                    FROM market_selection_mappings
                    WHERE market_source = 'BETFAIR_EXCHANGE' AND market_id = :market_id
                    """
                ),
                {"market_id": book.market_id},
            ).mappings().all()
        }
        for runner in book.runners:
            mapping = mappings.get(runner.selection_id)
            if mapping is None:
                quarantines += 1
                connection.execute(
                    text(
                        """
                        INSERT INTO market_mapping_quarantine (quarantine_id, quote_id, reason_code, detail)
                        VALUES (:quarantine_id, :quote_id, 'MISSING_EXACT_MAPPING', :detail)
                        ON CONFLICT (quarantine_id) DO NOTHING
                        """
                    ),
                    {
                        "quarantine_id": f"quarantine:{envelope.envelope_id}:{book.market_id}:{runner.selection_id}",
                        "quote_id": f"betfair:{envelope.envelope_id}:{book.market_id}:{runner.selection_id}",
                        "detail": "market book selection was not found in the projected catalogue mapping",
                    },
                )
                continue
            runner_status = "SCRATCHED" if runner.status in {"REMOVED", "SCRATCHED"} else "ACTIVE"
            mapping_dict = dict(mapping)
            best_back = max(runner.available_to_back, key=lambda level: level.price, default=None)
            best_lay = min(runner.available_to_lay, key=lambda level: level.price, default=None)
            for side, level in (("BACK", best_back), ("LAY", best_lay)):
                if level is None:
                    continue
                stable_id = hashlib.sha256(f"{envelope.envelope_id}:{book.market_id}:{runner.selection_id}:{side}".encode()).hexdigest()[:32]
                ingested = ingest_market_quote({
                    "quote_id": f"betfair:{stable_id}",
                    "mapping": mapping_dict,
                    "market_type": "WIN",
                    "price_type": "DECIMAL",
                    "quote_side": side,
                    "price_phase": "CLOSING" if book.status in {"CLOSED", "SETTLED", "SUSPENDED"} else "LIVE",
                    "runner_status": runner_status,
                    "price": level.price,
                    "source_timestamp": book.source_timestamp,
                    "retrieved_at": envelope.retrieved_at,
                    "in_play": book.in_play,
                    "size": level.size,
                    "liquidity": runner.total_matched or book.total_matched,
                    "entitlement_reference": envelope.licence_reference,
                    "source_receipt_id": receipt_id,
                    "data_mode": envelope.data_mode,
                    "rights_state": envelope.rights_state,
                })
                if ingested.quote is None:
                    quarantines += 1
                    connection.execute(
                        text(
                            """
                            INSERT INTO market_mapping_quarantine (quarantine_id, quote_id, reason_code, detail)
                            VALUES (:quarantine_id, :quote_id, 'INVALID_QUOTE', :detail)
                            ON CONFLICT (quarantine_id) DO NOTHING
                            """
                        ),
                        {
                            "quarantine_id": f"quarantine:{envelope.envelope_id}:{book.market_id}:{runner.selection_id}:{side}",
                            "quote_id": f"betfair:{stable_id}",
                            "detail": ingested.quarantine.detail if ingested.quarantine else "invalid quote",
                        },
                    )
                    continue
                quote = ingested.quote
                connection.execute(
                    text(
                        """
                        INSERT INTO market_quotes (
                            quote_id, code, race_id, field_revision, entry_id,
                            market_source, market_id, selection_id, market_type,
                            price_type, quote_side, price, source_timestamp, retrieved_at,
                            in_play, size, liquidity, entitlement_reference,
                            source_receipt_id, data_mode, rights_state, price_phase,
                            runner_status
                        ) VALUES (
                            :quote_id, :code, :race_id, :field_revision, :entry_id,
                            :market_source, :market_id, :selection_id, :market_type,
                            :price_type, :quote_side, :price, :source_timestamp, :retrieved_at,
                            :in_play, :size, :liquidity, :entitlement_reference,
                            :source_receipt_id, :data_mode, :rights_state, :price_phase,
                            :runner_status
                        ) ON CONFLICT (quote_id) DO NOTHING
                        """
                    ),
                    {
                        **{key: value for key, value in quote.model_dump().items() if key != "mapping"},
                        **quote.mapping.model_dump(),
                    },
                )
                quotes += 1
    return {"books": len(books), "quotes": quotes, "quarantines": quarantines}


def _required_text(value: object, label: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)) or not str(value).strip():
        raise BetfairBookParseError(f"book field {label} is missing")
    return str(value).strip()


def _number(value: object, label: str, *, positive: bool = False) -> float:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise BetfairBookParseError(f"book field {label} is not numeric") from exc
    if result != result or result in {float("inf"), float("-inf")} or (positive and result <= 0):
        raise BetfairBookParseError(f"book field {label} is invalid")
    return result


def _timestamp(value: object, label: str) -> datetime:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        parsed = datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc)
    else:
        raw = _required_text(value, label).replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise BetfairBookParseError(f"book field {label} is not an ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BetfairBookParseError(f"book field {label} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _levels(value: object, label: str) -> tuple[BetfairPriceLevel, ...]:
    if value in (None, []):
        return ()
    if not isinstance(value, list):
        raise BetfairBookParseError(f"book field {label} is not a list")
    levels: list[BetfairPriceLevel] = []
    for raw in value:
        if isinstance(raw, Mapping):
            price = raw.get("price")
            size = raw.get("size")
        elif isinstance(raw, (list, tuple)) and len(raw) >= 2:
            price, size = raw[0], raw[1]
        else:
            raise BetfairBookParseError(f"book field {label} contains an invalid level")
        levels.append(BetfairPriceLevel(_number(price, f"{label}.price", positive=True), _number(size, f"{label}.size", positive=True)))
    return tuple(levels)


def parse_betfair_market_book(envelope: RawEnvelope) -> tuple[BetfairMarketBook, ...]:
    if envelope.data_mode != "LICENSED" or envelope.rights_state != "APPROVED":
        raise BetfairBookParseError("Betfair market book requires a licensed, approved envelope")
    result = envelope.payload.get("result")
    if not isinstance(result, list):
        if envelope.payload.get("error"):
            raise BetfairBookParseError("Betfair market book returned a JSON-RPC error")
        raise BetfairBookParseError("Betfair market book result is not a list")
    books: list[BetfairMarketBook] = []
    for raw_market in result:
        if not isinstance(raw_market, Mapping):
            raise BetfairBookParseError("market book contains a non-object market")
        market_id = _required_text(raw_market.get("marketId"), "marketId")
        source_timestamp = _timestamp(raw_market.get("publishTime"), "publishTime")
        if source_timestamp > envelope.retrieved_at:
            raise BetfairBookParseError("book publishTime is later than retrieval")
        status = str(raw_market.get("status", "UNKNOWN")).strip().upper() or "UNKNOWN"
        market_definition = raw_market.get("marketDefinition")
        definition = market_definition if isinstance(market_definition, Mapping) else {}
        in_play = bool(raw_market.get("inplay", raw_market.get("inPlay", definition.get("inPlay", False))))
        total_matched_raw = raw_market.get("totalMatched")
        total_matched = None if total_matched_raw in (None, "") else _number(total_matched_raw, "totalMatched", positive=True)
        raw_runners = raw_market.get("runners")
        if not isinstance(raw_runners, list) or not raw_runners:
            raise BetfairBookParseError(f"market {market_id} has no runner book")
        runners: list[BetfairRunnerBook] = []
        seen: set[str] = set()
        for raw_runner in raw_runners:
            if not isinstance(raw_runner, Mapping):
                raise BetfairBookParseError(f"market {market_id} contains a non-object runner")
            selection_id = _required_text(raw_runner.get("selectionId"), "selectionId")
            if selection_id in seen:
                raise BetfairBookParseError(f"market {market_id} repeats selection {selection_id}")
            seen.add(selection_id)
            ex = raw_runner.get("ex")
            ex_mapping = ex if isinstance(ex, Mapping) else {}
            available_to_back = _levels(ex_mapping.get("availableToBack"), "availableToBack")
            available_to_lay = _levels(ex_mapping.get("availableToLay"), "availableToLay")
            traded_volume = _levels(ex_mapping.get("tradedVolume"), "tradedVolume")
            last_raw = raw_runner.get("lastPriceTraded")
            total_runner_raw = raw_runner.get("totalMatched")
            runners.append(BetfairRunnerBook(
                selection_id=selection_id,
                status=str(raw_runner.get("status", "ACTIVE")).strip().upper() or "ACTIVE",
                available_to_back=available_to_back,
                available_to_lay=available_to_lay,
                traded_volume=traded_volume,
                last_price_traded=None if last_raw in (None, "") else _number(last_raw, "lastPriceTraded", positive=True),
                total_matched=None if total_runner_raw in (None, "") else _number(total_runner_raw, "runner.totalMatched", positive=True),
            ))
        books.append(BetfairMarketBook(market_id, status, source_timestamp, in_play, total_matched, tuple(runners)))
    return tuple(books)


def normalise_betfair_market_book(envelope: RawEnvelope, catalogue: BetfairCatalogue) -> BetfairBookNormalisation:
    """Map book selections to catalogue identities and produce quote contracts."""

    books = parse_betfair_market_book(envelope)
    races = {race.market_id: race for race in catalogue.races}
    results: list[QuoteIngestResult] = []
    for book in books:
        race = races.get(book.market_id)
        if race is None:
            for runner in book.runners:
                results.append(QuoteIngestResult(quarantine={
                    "quote_id": f"{envelope.envelope_id}:{book.market_id}:{runner.selection_id}",
                    "reason_code": "MISSING_EXACT_MAPPING",
                    "detail": "market book market was not present in the catalogue capture",
                }))
            continue
        catalogue_runners = {runner.selection_id: runner for runner in race.runners}
        for runner in book.runners:
            catalog_runner = catalogue_runners.get(runner.selection_id)
            if catalog_runner is None:
                results.append(QuoteIngestResult(quarantine={
                    "quote_id": f"{envelope.envelope_id}:{book.market_id}:{runner.selection_id}",
                    "reason_code": "MISSING_EXACT_MAPPING",
                    "detail": "selection was not present in the catalogue capture",
                }))
                continue
            runner_status = "SCRATCHED" if runner.status in {"REMOVED", "SCRATCHED"} else "ACTIVE"
            mapping = {
                "mapping_id": f"betfair:{book.market_id}:{runner.selection_id}",
                "code": "THOROUGHBRED",
                "race_id": race.race_id,
                "field_revision": race.field_revision,
                "entry_id": catalog_runner.entry_id,
                "market_source": "BETFAIR_EXCHANGE",
                "market_id": book.market_id,
                "selection_id": runner.selection_id,
            }
            best_back = max(runner.available_to_back, key=lambda level: level.price, default=None)
            best_lay = min(runner.available_to_lay, key=lambda level: level.price, default=None)
            for side, level in (("BACK", best_back), ("LAY", best_lay)):
                if level is None:
                    continue
                stable_id = hashlib.sha256(f"{envelope.envelope_id}:{book.market_id}:{runner.selection_id}:{side}".encode()).hexdigest()[:32]
                raw: dict[str, Any] = {
                    "quote_id": f"betfair:{stable_id}",
                    "mapping": mapping,
                    "market_type": "WIN",
                    "price_type": "DECIMAL",
                    "quote_side": side,
                    "price_phase": "CLOSING" if book.status in {"CLOSED", "SETTLED", "SUSPENDED"} else "LIVE",
                    "runner_status": runner_status,
                    "price": level.price,
                    "source_timestamp": book.source_timestamp,
                    "retrieved_at": envelope.retrieved_at,
                    "in_play": book.in_play,
                    "size": level.size,
                    "liquidity": runner.total_matched or book.total_matched,
                    "entitlement_reference": envelope.licence_reference,
                    "source_receipt_id": envelope.envelope_id,
                    "data_mode": envelope.data_mode,
                    "rights_state": envelope.rights_state,
                }
                results.append(ingest_market_quote(raw))
    quotes = tuple(item.quote for item in results if item.quote is not None)
    quarantines = tuple(item.quarantine for item in results if item.quarantine is not None)
    return BetfairBookNormalisation(books, quotes, quarantines)
