"""Owner-triggered multi-provider live enrichment.

This is deliberately separate from the single-provider scheduled ingestion
runner. It fans out only to the four declared read-only providers, retains no
provider error body, and commits each provider projection atomically.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os

from sqlalchemy import create_engine

from app.betfair_live_projection import parse_betfair_catalogue, project_betfair_catalogue
from app.betfair_market_book import project_betfair_market_book
from app.database_config import sqlalchemy_database_url
from app.live_ingestion import persist_approved_live_envelope
from app.live_ingestion_health import record_ingestion_health
from app.live_projection import project_live_envelope
from app.live_provider_runtime import build_live_provider_handle
from app.runtime_config import load_runtime_config


def _date(value: str | None) -> str:
    selected = value or os.environ.get("NEXUS_LIVE_DATE", "").strip() or datetime.now(timezone.utc).date().isoformat()
    datetime.strptime(selected, "%Y-%m-%d")
    return selected


def _result(provider: str, operation: str, status: str, *, venue: str | None = None, detail: str | None = None, persistence: dict[str, object] | None = None, projection: dict[str, object] | None = None) -> dict[str, object]:
    payload: dict[str, object] = {"provider": provider, "operation": operation, "status": status}
    if venue:
        payload["venue"] = venue
    if detail:
        payload["detail"] = detail
    if persistence is not None:
        payload["persistence"] = persistence
    if projection is not None:
        payload["projection"] = projection
    return payload


def _safe_error_detail(exc: Exception) -> str:
    """Return bounded diagnostics without retaining provider response bodies or credentials."""

    message = " ".join(str(exc).split())
    for marker in ("X-API-Key", "Authorization", "X-Application", "X-Authentication", "api_key", "session_token"):
        if marker.lower() in message.lower():
            return type(exc).__name__
    return f"{type(exc).__name__}: {message[:180]}" if message else type(exc).__name__


def run_live_enrichment(*, date: str | None = None, venues: tuple[str, ...] = ()) -> dict[str, object]:
    runtime = load_runtime_config()
    if not runtime.live_enabled:
        raise RuntimeError("live enrichment requires NEXUS_DATA_MODE=LICENSED")
    if runtime.persistence != "postgres":
        raise RuntimeError("live enrichment requires NEXUS_API_PERSISTENCE=postgres")
    selected_date = _date(date)
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")
    engine = create_engine(sqlalchemy_database_url(database_url), pool_pre_ping=True, pool_size=1, max_overflow=0)
    outputs: list[dict[str, object]] = []
    betfair_market_ids: list[str] = []
    plans: tuple[tuple[str, str, str | None], ...] = (
        ("formfav", "LIST_MEETINGS", None),
        ("punters-edge", "GET_RESULTS", None),
        ("krok-odds", "LIST_MEETINGS", None),
        ("krok-odds", "GET_MARKETS", None),
    )
    if venues:
        plans += tuple(("formfav", "GET_RACES", venue) for venue in venues)
        plans += tuple(("betfair-exchange", "GET_MARKETS", venue) for venue in venues)
    else:
        plans += (("betfair-exchange", "GET_MARKETS", None),)

    try:
        for provider, operation, venue in plans:
            handle = None
            source_id = f"{provider}:{operation}"
            try:
                handle = build_live_provider_handle(provider)
                page = handle.adapter.fetch(
                    operation, code="THOROUGHBRED", date=selected_date, venue=venue,
                    page_size=100, approval=handle.config.approval,
                )
                if len(page.records) != 1:
                    raise RuntimeError("provider returned an unexpected envelope count")
                envelope = page.records[0]
                with engine.begin() as connection:
                    persistence = persist_approved_live_envelope(connection, envelope)
                    if provider == "formfav" and operation == "LIST_MEETINGS":
                        projection = {"races": 0, "entries": 0, "results": 0}
                    elif provider == "krok-odds" and operation == "GET_MARKETS":
                        projection = {"races": 0, "entries": 0, "results": 0}
                    elif provider == "betfair-exchange":
                        projection = project_betfair_catalogue(connection, envelope)
                        betfair_market_ids.extend(race.market_id for race in parse_betfair_catalogue(envelope).races)
                    else:
                        projection = project_live_envelope(connection, envelope)
                    record_ingestion_health(connection, source_id=source_id, checked_at=datetime.now(timezone.utc), success=True)
                outputs.append(_result(provider, operation, "SUCCESS", venue=venue, persistence=persistence, projection=projection))
            except Exception as exc:
                outputs.append(_result(provider, operation, "BLOCKED", venue=venue, detail=_safe_error_detail(exc)))
                try:
                    with engine.begin() as connection:
                        record_ingestion_health(connection, source_id=source_id, checked_at=datetime.now(timezone.utc), success=False)
                except Exception:
                    pass
            finally:
                if handle is not None:
                    handle.close()

        # A market-book request is intentionally a second phase: Betfair
        # requires explicit market IDs from the catalogue capture.
        for start in range(0, len(betfair_market_ids), 20):
            market_ids = tuple(dict.fromkeys(betfair_market_ids[start:start + 20]))
            handle = None
            try:
                handle = build_live_provider_handle("betfair-exchange")
                page = handle.adapter.fetch(
                    "GET_MARKETS", code="THOROUGHBRED", date=selected_date,
                    view="book", market_ids=market_ids, page_size=len(market_ids),
                    approval=handle.config.approval,
                )
                envelope = page.records[0]
                with engine.begin() as connection:
                    persistence = persist_approved_live_envelope(connection, envelope)
                    projection = project_betfair_market_book(connection, envelope)
                    record_ingestion_health(connection, source_id="betfair-exchange:GET_MARKETS:book", checked_at=datetime.now(timezone.utc), success=True)
                outputs.append(_result("betfair-exchange", "GET_MARKETS_BOOK", "SUCCESS", persistence=persistence, projection=projection))
            except Exception as exc:
                outputs.append(_result("betfair-exchange", "GET_MARKETS_BOOK", "BLOCKED", detail=_safe_error_detail(exc)))
                try:
                    with engine.begin() as connection:
                        record_ingestion_health(connection, source_id="betfair-exchange:GET_MARKETS:book", checked_at=datetime.now(timezone.utc), success=False)
                except Exception:
                    pass
            finally:
                if handle is not None:
                    handle.close()
    finally:
        engine.dispose()

    successful = sum(item["status"] == "SUCCESS" for item in outputs)
    if not successful:
        raise RuntimeError("no provider enrichment operation succeeded")
    return {"status": "LIVE_ENRICHMENT_COMPLETE", "date": selected_date, "results": outputs}
