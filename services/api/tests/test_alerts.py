from datetime import datetime, timedelta, timezone

import pytest

from app.alerts import AlertError, AlertRouter, ChangeEvent


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def event(event_id: str = "event-1", **overrides: object) -> ChangeEvent:
    values: dict[str, object] = {
        "event_id": event_id, "watch_id": "watch-1", "source_system": "source-a", "source_receipt_id": "receipt-1",
        "observed_at": NOW, "validity": "CONFIRMED", "material": True, "suppression_key": "watch-1:field-change",
        "cause": "confirmed field revision", "expires_at": NOW + timedelta(hours=1),
    }
    values.update(overrides)
    return ChangeEvent(**values)


def test_confirmed_material_events_create_source_linked_alerts() -> None:
    alert = AlertRouter().ingest(event(), NOW)

    assert alert is not None
    assert alert.source_system == "source-a"
    assert alert.source_receipt_id == "receipt-1"
    assert alert.status == "ACTIVE"


def test_unconfirmed_immaterial_and_expired_events_do_not_alert() -> None:
    router = AlertRouter()
    assert router.ingest(event("unconfirmed", validity="UNCONFIRMED"), NOW) is None
    assert router.ingest(event("immaterial", material=False), NOW) is None
    assert router.ingest(event("expired", observed_at=NOW - timedelta(hours=1), expires_at=NOW), NOW) is None
    assert router.active_alerts(NOW) == []


def test_suppression_key_deduplicates_replayed_events_until_expiry() -> None:
    router = AlertRouter()
    first = router.ingest(event(), NOW)
    duplicate = router.ingest(event("event-2"), NOW + timedelta(minutes=1))
    after_expiry = router.ingest(event("event-3", observed_at=NOW + timedelta(hours=2), expires_at=NOW + timedelta(hours=3)), NOW + timedelta(hours=2))

    assert duplicate == first
    assert after_expiry is not None and after_expiry.alert_id != first.alert_id


def test_replay_is_append_only_and_expiry_is_visible() -> None:
    router = AlertRouter()
    alerts = router.replay([event()], NOW)
    assert len(alerts) == 1
    assert router.active_alerts(NOW + timedelta(hours=2)) == []
    with pytest.raises(AlertError, match="append-only"):
        router.ingest(event(), NOW)


def test_event_requires_source_cause_and_timezone_aware_timestamps() -> None:
    with pytest.raises(AlertError, match="required"):
        AlertRouter().ingest(event(source_receipt_id=""), NOW)
    with pytest.raises(AlertError, match="timezone"):
        AlertRouter().ingest(event(observed_at=datetime(2026, 1, 15)), NOW)
