"""Run one bounded licensed provider ingestion into Render PostgreSQL.

This is intended for a Render Cron service. It performs one read-only provider
request, persists the approved envelope and projects canonical racing data in
one database transaction. It never prints provider payloads or credentials.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from sqlalchemy import create_engine  # noqa: E402

from app.live_ingestion import persist_approved_live_envelope  # noqa: E402
from app.live_projection import project_live_envelope  # noqa: E402
from app.live_provider_runtime import build_live_provider_handle  # noqa: E402
from app.runtime_config import load_runtime_config  # noqa: E402


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> int:
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

    date = os.environ.get("NEXUS_LIVE_DATE", "").strip() or datetime.now(timezone.utc).date().isoformat()
    venue = os.environ.get("NEXUS_LIVE_VENUE", "").strip() or None
    race_text = os.environ.get("NEXUS_LIVE_RACE", "").strip()
    race = int(race_text) if race_text else None
    database_url = _required("DATABASE_URL")

    handle = build_live_provider_handle(provider)
    try:
        page = handle.adapter.fetch(
            operation,  # type: ignore[arg-type]
            code=code,
            date=date,
            venue=venue,
            race=race,
            page_size=1,
            approval=handle.config.approval,
        )
        if len(page.records) != 1:
            raise RuntimeError("provider returned an unexpected envelope count")
        envelope = page.records[0]
        engine = create_engine(database_url, pool_pre_ping=True, pool_size=1, max_overflow=0)
        try:
            with engine.begin() as connection:
                persistence = persist_approved_live_envelope(connection, envelope)
                projection = project_live_envelope(connection, envelope)
        finally:
            engine.dispose()
        print({"status": "LIVE_INGESTION_SUCCESS", "provider": provider, "operation": operation, "date": date, "persistence": persistence, "projection": projection})
        return 0
    finally:
        handle.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as exc:
        print({"status": "LIVE_INGESTION_BLOCKED", "reason": str(exc)})
        raise SystemExit(2) from exc


