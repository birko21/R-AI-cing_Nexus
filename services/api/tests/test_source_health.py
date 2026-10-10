from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.capabilities import SourceCapabilityPolicy
from app.source_health import HealthObservation, SourceHealthMonitor


NOW = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)


def observation(**overrides: object) -> HealthObservation:
    values: dict[str, object] = {
        "source_id": "provider-pending",
        "checked_at": NOW,
        "expected_schema_version": "race-v1",
        "observed_schema_version": "race-v1",
        "last_success_at": NOW - timedelta(minutes=5),
        "latest_data_at": NOW - timedelta(hours=1),
        "expected_coverage": frozenset({"meetings", "races", "entries", "results"}),
        "observed_coverage": frozenset({"meetings", "races", "entries", "results"}),
    }
    values.update(overrides)
    return HealthObservation(**values)


def capability_policy() -> SourceCapabilityPolicy:
    return SourceCapabilityPolicy(
        source_id="provider-pending", data_mode="SCRAPED_PUBLIC", rights_state="APPROVED",
        approved_capabilities=frozenset({"STORE", "DISPLAY", "EXPORT"}),
    )


def test_healthy_source_has_no_disable_action() -> None:
    snapshot = SourceHealthMonitor().evaluate(observation())
    assert snapshot.status == "HEALTHY"
    assert snapshot.signals == ()
    assert not snapshot.capabilities_disabled


@pytest.mark.parametrize(
    "overrides,kind",
    [
        ({"observed_schema_version": "race-v2"}, "SCHEMA_DRIFT"),
        ({"last_success_at": NOW - timedelta(hours=1)}, "OUTAGE"),
        ({"latest_data_at": NOW - timedelta(days=2)}, "STALE_DATA"),
        ({"observed_coverage": frozenset({"meetings"})}, "COVERAGE_GAP"),
        ({"quota_remaining": 0}, "QUOTA_EXHAUSTED"),
    ],
)
def test_failure_signals_are_detected(overrides: dict[str, object], kind: str) -> None:
    snapshot = SourceHealthMonitor().evaluate(observation(**overrides))
    assert kind in {signal.kind for signal in snapshot.signals}


def test_critical_health_applies_kill_switch_without_mutating_policy_history() -> None:
    policy = capability_policy()
    snapshot = SourceHealthMonitor().evaluate(observation(observed_schema_version="race-v2"))

    disabled = SourceHealthMonitor().apply_kill_switch(policy, snapshot)

    assert snapshot.status == "DISABLED"
    assert disabled.enabled is False
    assert disabled.kill_switch_reason == "source health kill switch: SCHEMA_DRIFT"
    assert policy.enabled is True


def test_warning_health_degrades_but_does_not_disable_capabilities() -> None:
    snapshot = SourceHealthMonitor().evaluate(observation(late_revision_count=2, observed_coverage=frozenset({"meetings"})))
    disabled = SourceHealthMonitor().apply_kill_switch(capability_policy(), snapshot)

    assert snapshot.status == "DEGRADED"
    assert disabled.enabled is True


def test_mismatched_policy_source_is_rejected() -> None:
    snapshot = SourceHealthMonitor().evaluate(observation(observed_schema_version="race-v2"))
    other = capability_policy().model_copy(update={"source_id": "other"})
    with pytest.raises(ValueError, match="does not match"):
        SourceHealthMonitor().apply_kill_switch(other, snapshot)
