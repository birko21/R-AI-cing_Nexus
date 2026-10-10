from datetime import datetime, timezone

import pytest

from app.watchlists import WatchlistError, WatchlistRegistry


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def test_stable_runner_identity_survives_name_and_source_changes() -> None:
    registry = WatchlistRegistry()
    target = registry.create("THOROUGHBRED:stable:runner-1", "RUNNER", "THOROUGHBRED", "source-a", "runner-1", "Old Name", NOW)
    updated = registry.identity_change(target.watch_id, source_system="source-b", source_id="runner-1-new", name="Updated Name", now=NOW, detail="provider migration")

    assert updated.entity_id == target.entity_id
    assert updated.name == "Updated Name"
    assert [event.kind for event in registry.history(target.watch_id)] == ["CREATED", "SOURCE_CHANGED"]
    assert registry.history(target.watch_id)[0].name == "Old Name"


def test_pause_resume_and_remove_preserve_event_history() -> None:
    registry = WatchlistRegistry()
    target = registry.create("RACE:stable:race-1", "RACE", "HARNESS", "source", "race-1", "Race 1", NOW)
    registry.pause(target.watch_id, NOW)
    registry.resume(target.watch_id, NOW)
    removed = registry.remove(target.watch_id, NOW)

    assert removed.state == "REMOVED"
    assert [event.kind for event in registry.history(target.watch_id)] == ["CREATED", "PAUSED", "RESUMED", "REMOVED"]
    with pytest.raises(WatchlistError, match="historical"):
        registry.pause(target.watch_id, NOW)


def test_invalid_or_naive_identity_and_missing_watch_fail_closed() -> None:
    registry = WatchlistRegistry()
    with pytest.raises(WatchlistError, match="required"):
        registry.create("", "RUNNER", "THOROUGHBRED", "source", "id", "Name", NOW)
    with pytest.raises(WatchlistError, match="not found"):
        registry.current("missing")
    with pytest.raises(WatchlistError, match="timezone"):
        registry.create("runner", "RUNNER", "THOROUGHBRED", "source", "id", "Name", datetime(2026, 1, 15))
