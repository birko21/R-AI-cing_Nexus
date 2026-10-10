from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.operations import BudgetConfig, OperationsLedger, UsageEvent


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def event(job: str, spend: str, *, critical: bool = False, status: str = "SUCCESS") -> UsageEvent:
    return UsageEvent(job_id=job, provider="synthetic-provider", started_at=NOW, latency_ms=100, status=status, input_tokens=100, output_tokens=100, estimated_spend_aud=Decimal(spend), critical=critical)


def test_operations_snapshot_tracks_jobs_errors_latency_tokens_cost_and_alert_thresholds() -> None:
    ledger = OperationsLedger(BudgetConfig(daily_spend_aud=Decimal("1.00"), daily_tokens=10000))
    ledger.record(event("job-1", "0.50"))
    assert ledger.snapshot()["alert_level"] == "WARN_50"
    ledger.record(event("job-2", "0.30", status="ERROR"))
    snapshot = ledger.snapshot()
    assert snapshot["alert_level"] == "WARN_80"
    assert snapshot["jobs"] == 2 and snapshot["errors"] == 1 and snapshot["estimated_spend_aud"] == "0.80"


def test_cap_disables_noncritical_outbound_but_preserves_critical_controls() -> None:
    ledger = OperationsLedger(BudgetConfig(daily_spend_aud=Decimal("1.00")))
    ledger.record(event("job-1", "1.00"))
    assert ledger.snapshot()["alert_level"] == "CAP_100"
    assert ledger.outbound_allowed("provider", critical=False) is False
    assert ledger.outbound_allowed("provider", critical=True) is True
    ledger.disable_provider("provider")
    assert ledger.outbound_allowed("provider", critical=True) is False


def test_usage_and_budget_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        UsageEvent(job_id="j", provider="p", started_at=datetime(2026, 1, 15), latency_ms=0, status="SUCCESS", input_tokens=0, output_tokens=0, estimated_spend_aud=Decimal("0"))
    with pytest.raises(ValueError, match="positive"):
        BudgetConfig(daily_tokens=0)
