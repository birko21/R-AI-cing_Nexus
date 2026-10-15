"""Run one bounded licensed-provider ingestion.

The runner is shared by the local/CI command and the optional protected HTTP
trigger. It returns only safe counters and identifiers; provider payloads and
credentials never enter the response or logs.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os

from sqlalchemy import create_engine

from app.database_config import sqlalchemy_database_url
from app.live_ingestion import persist_approved_live_envelope
from app.live_projection import project_live_envelope
from app.live_provider_runtime import build_live_provider_handle
from app.runtime_config import load_runtime_config


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def run_live_ingestion(
    *,
    date: str | None = None,
    venue: str | None = None,
    race: int | None = None,
) -> dict[str, object]:
    runtime = load_runtime_config()
    if not runtime.live_enabled:
        raise RuntimeError("live ingestion requires NEXUS_DATA_MODE=LICENSED")
    if runtime.persistence != "postgres":
        raise RuntimeError("live ingestion requires NEXUS_API_PERSISTENCE=postgres")

    provider = _required("NEXUS_LIVE_PROVIDER")
    operation = _required("NEXUS_LIVE_OPERATION")
    code = _required("NEXUS_LIVE_CODE")
    if provider != runtime.live_provider or operation not in runtime.live_operations or code not in runtime.live_codes:
        raise RuntimeError("live ingestion request is outside the configured scope")
    if operation == "ACCOUNT_METADATA_READ":
        raise RuntimeError("account metadata is not a canonical racing ingestion operation")

    selected_date = date or os.environ.get("NEXUS_LIVE_DATE", "").strip() or datetime.now(timezone.utc).date().isoformat()
    selected_venue = venue or os.environ.get("NEXUS_LIVE_VENUE", "").strip() or None
    selected_race = race
    if selected_race is None:
        race_text = os.environ.get("NEXUS_LIVE_RACE", "").strip()
        selected_race = int(race_text) if race_text else None
    database_url = _required("DATABASE_URL")

    handle = build_live_provider_handle(provider)
    try:
        page = handle.adapter.fetch(
            operation,  # type: ignore[arg-type]
            code=code,
            date=selected_date,
            venue=selected_venue,
            race=selected_race,
            page_size=1,
            approval=handle.config.approval,
        )
        if len(page.records) != 1:
            raise RuntimeError("provider returned an unexpected envelope count")
        envelope = page.records[0]
        engine = create_engine(sqlalchemy_database_url(database_url), pool_pre_ping=True, pool_size=1, max_overflow=0)
        try:
            with engine.begin() as connection:
                persistence = persist_approved_live_envelope(connection, envelope)
                projection = project_live_envelope(connection, envelope)
        finally:
            engine.dispose()
        return {
            "status": "LIVE_INGESTION_SUCCESS",
            "provider": provider,
            "operation": operation,
            "code": code,
            "date": selected_date,
            "persistence": persistence,
            "projection": projection,
        }
    finally:
        handle.close()
