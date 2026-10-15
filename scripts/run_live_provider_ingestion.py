"""Run one bounded licensed provider ingestion into Render PostgreSQL.

This is intended for a Render Cron service. It performs one read-only provider
request, persists the approved envelope and projects canonical racing data in
one database transaction. It never prints provider payloads or credentials.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.live_ingestion_runner import run_live_ingestion  # noqa: E402


def main() -> int:
    print(run_live_ingestion())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as exc:
        print({"status": "LIVE_INGESTION_BLOCKED", "reason": str(exc)})
        raise SystemExit(2) from exc

