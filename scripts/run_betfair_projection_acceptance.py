"""Exercise the licensed Betfair catalogue projection against disposable PostgreSQL.

This uses a fixed contract-shaped response, not a provider response. It proves
the SQL transaction and canonical projection against PostgreSQL while keeping
the external provider disabled.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.betfair_live_projection import project_betfair_catalogue  # noqa: E402
from app.database_safety import validate_disposable_database_url  # noqa: E402
from app.live_ingestion import persist_approved_live_envelope  # noqa: E402
from app.provenance import RawEnvelope, payload_sha256  # noqa: E402


def main() -> None:
    target = validate_disposable_database_url()
    payload = {
        "jsonrpc": "2.0",
        "result": [
            {
                "marketId": "1.9001",
                "marketName": "R2 1200m Maiden",
                "marketStartTime": "2026-10-12T04:30:00Z",
                "event": {"id": "acceptance-event-1", "name": "Randwick"},
                "runners": [
                    {"selectionId": 101, "runnerName": "Acceptance One", "sortPriority": 1},
                    {"selectionId": 102, "runnerName": "Acceptance Two", "sortPriority": 2},
                ],
            }
        ],
    }
    now = datetime.now(timezone.utc)
    envelope = RawEnvelope(
        envelope_id="betfair-projection-acceptance-1",
        source_identifier="betfair-exchange:GET_MARKETS",
        payload=payload,
        payload_sha256=payload_sha256(payload),
        schema_version="provider-response-v1",
        retrieved_at=now,
        first_observed_at=now,
        data_mode="LICENSED",
        rights_state="APPROVED",
        licence_reference="acceptance-only",
    )
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with engine.begin() as connection:
            receipt = persist_approved_live_envelope(connection, envelope)
            projection = project_betfair_catalogue(connection, envelope)
    finally:
        engine.dispose()
    print(json.dumps({"status": "POSTGRES_BETFAIR_PROJECTION_ACCEPTANCE_PASS", "target": target.database, "receipt": receipt, "projection": projection}, sort_keys=True))


if __name__ == "__main__":
    main()
