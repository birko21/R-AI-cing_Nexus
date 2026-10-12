"""Exercise canonical PostgreSQL projections, API reads and durable selections."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys

from sqlalchemy import create_engine


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.baseline import BaselineRace, BaselineRunner, build_b0_forecast  # noqa: E402
from app.betfair_mock import SyntheticBetfairExchangeAdapter  # noqa: E402
from app.catalog_repository import PostgresCatalogRepository  # noqa: E402
from app.contracts import SelectionAddendumCreate, SelectionCreate  # noqa: E402
from app.database_safety import validate_disposable_database_url  # noqa: E402
from app.forecast_archive import create_forecast_manifest  # noqa: E402
from app.selection_journal import PostgresSelectionJournal  # noqa: E402
from app.synthetic_projection import append_forecast_manifest, project_synthetic_market  # noqa: E402


def main() -> None:
    validate_disposable_database_url()
    engine = create_engine(os.environ["DATABASE_URL"])
    adapter = SyntheticBetfairExchangeAdapter()
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        for market in adapter.markets:
            envelope = adapter.fetch("GET_MARKETS", code=market.code).records[0]
            project_synthetic_market(connection, market, envelope)
            cutoff = market.market_start_time - timedelta(minutes=5)
            forecast = build_b0_forecast(
                BaselineRace(
                    race_id=market.race_id,
                    code=market.code,
                    field_revision=market.field_revision,
                    field_status="FINAL_FIELDS",
                    runners=tuple(
                        BaselineRunner(entry_id=runner.entry_id, number=index)
                        for index, runner in enumerate(market.runners, start=1)
                    ),
                ),
                cutoff=cutoff,
                manifest_checksum=envelope.payload_sha256,
            )
            manifest = create_forecast_manifest(
                forecast_id=forecast.forecast_id,
                race_id=forecast.race_id,
                field_revision=forecast.field_revision,
                cutoff=forecast.cutoff,
                feature_snapshot={"source_envelope_id": envelope.envelope_id, "payload_sha256": envelope.payload_sha256},
                model_descriptor={"model_id": forecast.model_id, "model_version": forecast.model_version},
                active_runner_ids=[runner.entry_id for runner in market.runners],
                data_mode=forecast.data_mode,
                diagnostic_flags=forecast.diagnostics,
                output=forecast.to_dict(),
            )
            append_forecast_manifest(connection, manifest)

    catalog = PostgresCatalogRepository(engine)
    meetings, meetings_more = catalog.list_meetings(limit=10, offset=0, as_of=now)
    race = catalog.get_race("race:1", as_of=now)
    entries, entries_more = catalog.list_entries("race:1", limit=10, offset=0, as_of=now)
    forecasts, forecasts_more = catalog.list_forecasts("race:1", limit=10, offset=0, as_of=now)
    assert len(meetings) == 3 and meetings_more is False
    assert race is not None and race.data_mode == "SYNTHETIC_ONLY"
    assert len(entries) == 3 and entries_more is False
    assert len(forecasts) == 1 and forecasts_more is False
    assert sum(forecasts[0].probabilities.values()) == 1.0

    journal = PostgresSelectionJournal(engine)
    selection = journal.create(
        "acceptance-owner",
        SelectionCreate(race_id="race:1", field_revision="RIL-Synthetic-1", selection_type="PASS", rationale="acceptance proof"),
    )
    addendum = journal.addendum("acceptance-owner", selection.selection_id, SelectionAddendumCreate(note="append-only persistence proof"))
    assert any(item.selection_id == selection.selection_id for item in journal.list_for_user("acceptance-owner"))
    assert journal.addenda_for("acceptance-owner", selection.selection_id)[0].addendum_id == addendum.addendum_id

    print(json.dumps({
        "status": "PASS",
        "meetings": len(meetings),
        "entries": len(entries),
        "forecasts": len(forecasts),
        "selection_persisted": True,
        "data_mode": "SYNTHETIC_ONLY",
        "external_connectivity": False,
        "wagering_enabled": False,
    }, indent=2))


if __name__ == "__main__":
    main()
