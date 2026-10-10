from datetime import datetime, timezone

import pytest

from app.capabilities import CapabilityDenied, CapabilityGuard, SourceCapabilityPolicy, source_is_disabled


NOW = datetime(2026, 1, 10, tzinfo=timezone.utc)


def policy(**overrides) -> SourceCapabilityPolicy:
    values = {
        "source_id": "synthetic-fixture",
        "data_mode": "SYNTHETIC_ONLY",
        "rights_state": "SYNTHETIC",
        "approved_capabilities": frozenset({"STORE", "DISPLAY", "EXPORT"}),
    }
    values.update(overrides)
    return SourceCapabilityPolicy(**values)


def test_synthetic_rights_allow_explicit_local_capabilities_only() -> None:
    guard = CapabilityGuard()
    assert guard.decide(policy(), "STORE", NOW).decision == "ALLOWED"
    assert guard.decide(policy(), "DISPLAY", NOW).decision == "ALLOWED"
    assert guard.decide(policy(), "EXPORT", NOW).decision == "ALLOWED"
    assert guard.decide(policy(), "LLM", NOW).decision == "NOT_AVAILABLE"
    assert guard.decide(policy(), "SCRAPE", NOW).decision == "NOT_AVAILABLE"


def test_unapproved_or_unassessed_sources_are_not_entitled() -> None:
    guard = CapabilityGuard()
    scraped = policy(data_mode="SCRAPED_PUBLIC", rights_state="UNASSESSED")
    assert guard.decide(scraped, "DISPLAY", NOW).decision == "NOT_ENTITLED"
    licensed = policy(data_mode="LICENSED", rights_state="RESTRICTED")
    assert guard.decide(licensed, "STORE", NOW).decision == "NOT_ENTITLED"


def test_kill_switch_and_retention_expiry_are_not_available() -> None:
    guard = CapabilityGuard()
    disabled = policy(enabled=False, kill_switch_reason="provider revoked permission")
    assert source_is_disabled(disabled)
    assert guard.decide(disabled, "DISPLAY", NOW).decision == "NOT_AVAILABLE"

    expired = policy(retention_until=datetime(2026, 1, 9, tzinfo=timezone.utc))
    assert guard.decide(expired, "EXPORT", NOW).decision == "NOT_AVAILABLE"


def test_require_raises_before_operation_can_proceed() -> None:
    with pytest.raises(CapabilityDenied, match="NOT_AVAILABLE"):
        CapabilityGuard().require(policy(), "LLM", NOW)
