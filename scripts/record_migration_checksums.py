from __future__ import annotations

import hashlib
import os
from pathlib import Path

from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "migrations" / "versions"


def migration_hashes() -> list[tuple[str, str, str]]:
    rows = []
    for path in sorted(MIGRATION_DIR.glob("*.py")):
        revision = path.stem
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append((revision, str(path.relative_to(ROOT)).replace("\\", "/"), digest))
    return rows


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL must be set")

    engine = create_engine(database_url)
    with engine.begin() as connection:
        for revision, filename, digest in migration_hashes():
            connection.execute(
                text(
                    """
                    INSERT INTO schema_migration_checksums (revision, filename, sha256)
                    VALUES (:revision, :filename, :sha256)
                    ON CONFLICT (revision) DO NOTHING
                    """
                ),
                {"revision": revision, "filename": filename, "sha256": digest},
            )

    print(f"RECORDED MIGRATION CHECKSUMS: {len(migration_hashes())}")


if __name__ == "__main__":
    main()
