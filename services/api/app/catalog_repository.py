"""Provider-neutral catalog repositories for API reads.

The local default is a deterministic synthetic repository so the API is useful
without credentials or a database. An explicit PostgreSQL repository can be
selected by a future deployment composition without changing the API contract.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol

from sqlalchemy import Engine, text

from app.baseline import BaselineRace, BaselineRunner, build_b0_forecast
from app.betfair_mock import synthetic_betfair_markets
from app.contracts import Entry, Forecast, Meeting, Race


class CatalogRepository(Protocol):
    def list_meetings(self, *, limit: int, offset: int, as_of: datetime) -> tuple[list[Meeting], bool]: ...
    def get_race(self, race_id: str, *, as_of: datetime) -> Race | None: ...
    def list_entries(self, race_id: str, *, limit: int, offset: int, as_of: datetime) -> tuple[list[Entry], bool]: ...
    def list_forecasts(self, race_id: str, *, limit: int, offset: int, as_of: datetime) -> tuple[list[Forecast], bool]: ...


def _synthetic_meeting_id(code: str) -> str:
    return f"synthetic-meeting:{code.lower()}"


class SyntheticCatalogRepository:
    """Deterministic read projection over the checked-in synthetic market lane."""

    def __init__(self) -> None:
        self._markets = synthetic_betfair_markets()
        self._meetings = [
            Meeting(
                meeting_id=_synthetic_meeting_id(market.code),
                code=market.code,
                name=market.venue,
                country="AUS",
                scheduled_date=market.market_start_time,
                data_mode="SYNTHETIC_ONLY",
            )
            for market in self._markets
        ]

    def list_meetings(self, *, limit: int, offset: int, as_of: datetime) -> tuple[list[Meeting], bool]:
        visible = [meeting for meeting in self._meetings if meeting.scheduled_date <= as_of]
        page = visible[offset:offset + limit]
        return page, offset + len(page) < len(visible)

    def get_race(self, race_id: str, *, as_of: datetime) -> Race | None:
        market = next((item for item in self._markets if item.race_id == race_id), None)
        if market is None or market.market_start_time > as_of:
            return None
        return Race(
            race_id=market.race_id,
            meeting_id=_synthetic_meeting_id(market.code),
            race_number=int(market.race_id.rsplit(":", 1)[-1]),
            status="FINAL_FIELDS",
            field_revision=market.field_revision,
            data_mode="SYNTHETIC_ONLY",
            source_receipt_id=f"synthetic://{market.market_id}",
            as_of=as_of,
        )

    def list_entries(self, race_id: str, *, limit: int, offset: int, as_of: datetime) -> tuple[list[Entry], bool]:
        market = next((item for item in self._markets if item.race_id == race_id), None)
        if market is None or market.market_start_time > as_of:
            return [], False
        entries = [
            Entry(
                entry_id=runner.entry_id,
                race_id=market.race_id,
                participant_id=runner.entry_id,
                number=number,
                name=runner.runner_name,
                status="ACTIVE" if runner.status == "ACTIVE" else "SCRATCHED",
                data_mode="SYNTHETIC_ONLY",
            )
            for number, runner in enumerate(market.runners, start=1)
        ]
        page = entries[offset:offset + limit]
        return page, offset + len(page) < len(entries)

    def list_forecasts(self, race_id: str, *, limit: int, offset: int, as_of: datetime) -> tuple[list[Forecast], bool]:
        market = next((item for item in self._markets if item.race_id == race_id), None)
        if market is None or market.market_start_time > as_of:
            return [], False
        cutoff = market.market_start_time - timedelta(minutes=5)
        forecast = build_b0_forecast(
            BaselineRace(
                race_id=market.race_id,
                code=market.code,
                field_revision=market.field_revision,
                field_status="FINAL_FIELDS",
                runners=tuple(
                    BaselineRunner(entry_id=runner.entry_id, number=number)
                    for number, runner in enumerate(market.runners, start=1)
                ),
            ),
            cutoff=cutoff,
            manifest_checksum=f"synthetic:{market.market_id}",
        )
        records = [
            Forecast(
                forecast_id=forecast.forecast_id,
                race_id=forecast.race_id,
                field_revision=forecast.field_revision,
                cutoff=cutoff,
                model_version=forecast.model_version,
                probabilities={runner.entry_id: runner.probability for runner in forecast.runners if runner.probability is not None},
                data_mode="SYNTHETIC_ONLY",
                diagnostic_flags=list(forecast.diagnostics),
            )
        ] if forecast.status == "READY" and cutoff <= as_of else []
        page = records[offset:offset + limit]
        return page, offset + len(page) < len(records)


class PostgresCatalogRepository:
    """Read-only projection repository for the canonical PostgreSQL schema."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def list_meetings(self, *, limit: int, offset: int, as_of: datetime) -> tuple[list[Meeting], bool]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT meeting_id, code, name, country, scheduled_at, data_mode
                    FROM meetings
                    WHERE first_observed_at <= :as_of
                    ORDER BY scheduled_at, meeting_id
                    LIMIT :fetch_limit OFFSET :offset
                    """
                ),
                {"as_of": as_of, "fetch_limit": limit + 1, "offset": offset},
            ).mappings().all()
        return [Meeting(meeting_id=row["meeting_id"], code=row["code"], name=row["name"], country=row["country"], scheduled_date=row["scheduled_at"], data_mode=row["data_mode"]) for row in rows[:limit]], len(rows) > limit

    def get_race(self, race_id: str, *, as_of: datetime) -> Race | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT race_id, meeting_id, race_number, status, field_revision,
                           data_mode, source_receipt_id
                    FROM race_revisions
                    WHERE race_id = :race_id
                      AND effective_from <= :as_of
                      AND (effective_to IS NULL OR effective_to > :as_of)
                    ORDER BY effective_from DESC
                    LIMIT 1
                    """
                ),
                {"race_id": race_id, "as_of": as_of},
            ).mappings().first()
        if row is None:
            return None
        return Race(**dict(row), as_of=as_of)

    def list_entries(self, race_id: str, *, limit: int, offset: int, as_of: datetime) -> tuple[list[Entry], bool]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT e.entry_id, r.race_id, e.participant_id, e.number,
                           p.name, e.status, e.data_mode
                    FROM entry_revisions e
                    JOIN race_revisions r ON r.race_revision_id = e.race_revision_id
                    JOIN participants p ON p.participant_id = e.participant_id
                    WHERE r.race_id = :race_id
                      AND e.effective_from <= :as_of
                      AND (e.effective_to IS NULL OR e.effective_to > :as_of)
                    ORDER BY e.number, e.entry_id
                    LIMIT :fetch_limit OFFSET :offset
                    """
                ),
                {"race_id": race_id, "as_of": as_of, "fetch_limit": limit + 1, "offset": offset},
            ).mappings().all()
        return [Entry(**dict(row)) for row in rows[:limit]], len(rows) > limit

    def list_forecasts(self, race_id: str, *, limit: int, offset: int, as_of: datetime) -> tuple[list[Forecast], bool]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT forecast_id, race_id, field_revision, cutoff_at,
                           model_version, probabilities, data_mode
                    FROM forecast_archives
                    WHERE race_id = :race_id AND created_at <= :as_of
                    ORDER BY cutoff_at DESC, forecast_id
                    LIMIT :fetch_limit OFFSET :offset
                    """
                ),
                {"race_id": race_id, "as_of": as_of, "fetch_limit": limit + 1, "offset": offset},
            ).mappings().all()
        return [Forecast(forecast_id=row["forecast_id"], race_id=row["race_id"], field_revision=row["field_revision"], cutoff=row["cutoff_at"], model_version=row["model_version"], probabilities=row["probabilities"], data_mode=row["data_mode"]) for row in rows[:limit]], len(rows) > limit


def offset_from_cursor(cursor: str | None, *, as_of: datetime) -> int:
    if cursor is None:
        return 0
    from app.pagination import decode_cursor

    return int(decode_cursor(cursor, as_of)["offset"])
