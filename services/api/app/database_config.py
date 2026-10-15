"""Database connection helpers shared by the API and live-ingestion paths."""

from __future__ import annotations


def sqlalchemy_database_url(database_url: str) -> str:
    """Use the installed psycopg 3 driver for standard PostgreSQL URLs."""

    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    return database_url
