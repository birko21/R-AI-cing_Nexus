from __future__ import annotations

import hashlib
import os
from pathlib import Path

from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "migrations" / "versions"


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL must be set")

    expected = {}
    for path in sorted(MIGRATION_DIR.glob("*.py")):
        revision = path.stem
        expected[revision] = (
            str(path.relative_to(ROOT)).replace("\\", "/"),
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )

    engine = create_engine(database_url)
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT revision, filename, sha256 FROM schema_migration_checksums ORDER BY revision")
        ).mappings()
        recorded = {row["revision"]: (row["filename"], row["sha256"]) for row in rows}

    if recorded != expected:
        raise SystemExit(f"MIGRATION CHECKSUM MISMATCH: recorded={recorded} expected={expected}")

    print(f"MIGRATION CHECKSUMS VALID: {len(recorded)}")


if __name__ == "__main__":
    main()
