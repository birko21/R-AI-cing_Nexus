"""Fail-closed validation for local disposable PostgreSQL targets."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re

from sqlalchemy.engine.url import make_url


DISPOSABLE_CONFIRMATION = "RACING_INTELLIGENCE_DB_DISPOSABLE"
_SAFE_DATABASE_NAME = re.compile(r"(?:dev|test|smoke|local|disposable)$", re.IGNORECASE)
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass(frozen=True)
class DisposableDatabaseTarget:
    driver: str
    host: str
    port: int | None
    database: str


def validate_disposable_database_url(
    database_url: str | None = None,
    *,
    confirmation: str | None = None,
) -> DisposableDatabaseTarget:
    """Validate a migration target without logging credentials or opening a connection."""

    raw_url = database_url or os.environ.get("DATABASE_URL")
    if not raw_url:
        raise ValueError("DATABASE_URL must be set to a disposable local PostgreSQL database")
    try:
        url = make_url(raw_url)
    except Exception as exc:  # SQLAlchemy may raise several URL parsing errors.
        raise ValueError("DATABASE_URL is not a valid SQLAlchemy database URL") from exc
    if url.drivername not in {"postgresql", "postgresql+psycopg", "postgresql+psycopg2"}:
        raise ValueError("DATABASE_URL must use a PostgreSQL driver")
    host = url.host or ""
    if host not in _LOOPBACK_HOSTS:
        raise ValueError("database smoke requires a loopback PostgreSQL host")
    database = url.database or ""
    if not _SAFE_DATABASE_NAME.search(database):
        raise ValueError("database name must end with dev, test, smoke, local or disposable")
    expected_confirmation = confirmation or os.environ.get(DISPOSABLE_CONFIRMATION)
    if expected_confirmation != "1":
        raise ValueError(f"set {DISPOSABLE_CONFIRMATION}=1 to confirm the database is disposable")
    return DisposableDatabaseTarget(url.drivername, host, url.port, database)
