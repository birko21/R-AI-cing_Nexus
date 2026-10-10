"""Failure detection and kill-switch decisions for provider sources."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from app.capabilities import SourceCapabilityPolicy


HealthKind = Literal["SCHEMA_DRIFT", "LATE_REVISION", "OUTAGE", "STALE_DATA", "COVERAGE_GAP", "QUOTA_EXHAUSTED"]
HealthSeverity = Literal["WARNING", "CRITICAL"]
HealthStatus = Literal["HEALTHY", "DEGRADED", "DISABLED"]


@dataclass(frozen=True)
class SourceHealthPolicy:
    outage_after: timedelta = timedelta(minutes=30)
    stale_after: timedelta = timedelta(hours=6)
    minimum_coverage_ratio: float = 1.0

    def __post_init__(self) -> None:
        if self.outage_after <= timedelta(0) or self.stale_after <= timedelta(0):
            raise ValueError("health thresholds must be positive")
        if not 0 < self.minimum_coverage_ratio <= 1:
            raise ValueError("minimum coverage ratio must be between 0 and 1")


@dataclass(frozen=True)
class HealthObservation:
    source_id: str
    checked_at: datetime
    expected_schema_version: str
    observed_schema_version: str
    last_success_at: datetime | None
    latest_data_at: datetime | None
    expected_coverage: frozenset[str]
    observed_coverage: frozenset[str]
    late_revision_count: int = 0
    quota_remaining: int | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.expected_schema_version.strip() or not self.observed_schema_version.strip():
            raise ValueError("source health identity and schema versions are required")
        for name, value in (("checked_at", self.checked_at), ("last_success_at", self.last_success_at), ("latest_data_at", self.latest_data_at)):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError(f"{name} must be timezone-aware")
        if self.late_revision_count < 0 or (self.quota_remaining is not None and self.quota_remaining < 0):
            raise ValueError("health counters cannot be negative")


@dataclass(frozen=True)
class HealthSignal:
    kind: HealthKind
    severity: HealthSeverity
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "severity": self.severity, "detail": self.detail}


@dataclass(frozen=True)
class SourceHealthSnapshot:
    source_id: str
    checked_at: datetime
    status: HealthStatus
    signals: tuple[HealthSignal, ...]
    capabilities_disabled: bool
    kill_switch_reason: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "checked_at": self.checked_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": self.status,
            "signals": [signal.to_dict() for signal in self.signals],
            "capabilities_disabled": self.capabilities_disabled,
            "kill_switch_reason": self.kill_switch_reason,
        }


class SourceHealthMonitor:
    def __init__(self, policy: SourceHealthPolicy | None = None) -> None:
        self.policy = policy or SourceHealthPolicy()

    def evaluate(self, observation: HealthObservation) -> SourceHealthSnapshot:
        signals: list[HealthSignal] = []
        if observation.expected_schema_version != observation.observed_schema_version:
            signals.append(HealthSignal("SCHEMA_DRIFT", "CRITICAL", "observed schema differs from the declared adapter schema"))
        if observation.late_revision_count:
            signals.append(HealthSignal("LATE_REVISION", "WARNING", f"{observation.late_revision_count} late revision(s) observed"))
        if observation.last_success_at is None or observation.checked_at - observation.last_success_at > self.policy.outage_after:
            signals.append(HealthSignal("OUTAGE", "CRITICAL", "no successful source response within the outage threshold"))
        if observation.latest_data_at is None or observation.checked_at - observation.latest_data_at > self.policy.stale_after:
            signals.append(HealthSignal("STALE_DATA", "WARNING", "latest source data exceeds the staleness threshold"))
        coverage_ratio = 1.0 if not observation.expected_coverage else len(observation.expected_coverage & observation.observed_coverage) / len(observation.expected_coverage)
        if coverage_ratio < self.policy.minimum_coverage_ratio:
            signals.append(HealthSignal("COVERAGE_GAP", "WARNING", f"coverage ratio {coverage_ratio:.3f} is below the configured minimum"))
        if observation.quota_remaining == 0:
            signals.append(HealthSignal("QUOTA_EXHAUSTED", "CRITICAL", "provider quota is exhausted"))
        critical = any(signal.severity == "CRITICAL" for signal in signals)
        status: HealthStatus = "DISABLED" if critical else "DEGRADED" if signals else "HEALTHY"
        reason = "; ".join(signal.kind for signal in signals if signal.severity == "CRITICAL") or None
        return SourceHealthSnapshot(observation.source_id, observation.checked_at, status, tuple(signals), critical, reason)

    def apply_kill_switch(self, policy: SourceCapabilityPolicy, snapshot: SourceHealthSnapshot) -> SourceCapabilityPolicy:
        if policy.source_id != snapshot.source_id:
            raise ValueError("health snapshot source does not match capability policy")
        if not snapshot.capabilities_disabled:
            return policy
        return policy.model_copy(update={"enabled": False, "kill_switch_reason": f"source health kill switch: {snapshot.kill_switch_reason}"})
