"""Validate DATABASE_URL is an explicitly disposable loopback PostgreSQL target."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.database_safety import validate_disposable_database_url  # noqa: E402


def main() -> None:
    try:
        target = validate_disposable_database_url()
    except ValueError as exc:
        raise SystemExit(f"DATABASE TARGET REJECTED: {exc}") from exc
    print(json.dumps({"driver": target.driver, "host": target.host, "port": target.port, "database": target.database}, sort_keys=True))


if __name__ == "__main__":
    main()
