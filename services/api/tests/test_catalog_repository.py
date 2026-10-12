from datetime import datetime, timezone

from app.catalog_repository import SyntheticCatalogRepository


AS_OF = datetime(2026, 1, 15, 2, 0, tzinfo=timezone.utc)


def test_synthetic_catalog_repository_serves_real_race_entries_and_forecast() -> None:
    repository = SyntheticCatalogRepository()

    meetings, has_more = repository.list_meetings(limit=2, offset=0, as_of=AS_OF)
    assert len(meetings) == 2
    assert has_more is True
    assert meetings[0].data_mode == "SYNTHETIC_ONLY"

    race = repository.get_race("race:1", as_of=AS_OF)
    assert race is not None
    assert race.status == "FINAL_FIELDS"

    entries, entries_more = repository.list_entries("race:1", limit=2, offset=0, as_of=AS_OF)
    assert len(entries) == 2
    assert entries_more is True
    assert entries[0].race_id == "race:1"

    forecasts, forecast_more = repository.list_forecasts("race:1", limit=10, offset=0, as_of=AS_OF)
    assert len(forecasts) == 1
    assert forecast_more is False
    assert sum(forecasts[0].probabilities.values()) == 1.0


def test_synthetic_catalog_repository_is_point_in_time() -> None:
    repository = SyntheticCatalogRepository()
    before_start = datetime(2026, 1, 15, 0, 59, 59, tzinfo=timezone.utc)

    assert repository.get_race("race:1", as_of=before_start) is None
    entries, _ = repository.list_entries("race:1", limit=100, offset=0, as_of=before_start)
    assert entries == []
