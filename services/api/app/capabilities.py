from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Capability = Literal["STORE", "DISPLAY", "EXPORT", "LLM", "SCRAPE"]
Decision = Literal["ALLOWED", "NOT_AVAILABLE", "NOT_ENTITLED"]


class SourceCapabilityPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]
    rights_state: Literal["SYNTHETIC", "UNASSESSED", "APPROVED", "RESTRICTED", "REJECTED"]
    approved_capabilities: frozenset[Capability] = frozenset()
    enabled: bool = True
    kill_switch_reason: str | None = None
    retention_until: datetime | None = None


@dataclass(frozen=True)
class CapabilityDecision:
    capability: Capability
    decision: Decision
    reason: str


class CapabilityDenied(PermissionError):
    def __init__(self, decision: CapabilityDecision):
        self.decision = decision
        super().__init__(f"{decision.decision}: {decision.reason}")


class CapabilityGuard:
    def decide(self, policy: SourceCapabilityPolicy, capability: Capability, now: datetime | None = None) -> CapabilityDecision:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if not policy.enabled:
            return CapabilityDecision(capability, "NOT_AVAILABLE", policy.kill_switch_reason or "source is disabled")
        if policy.retention_until and current >= policy.retention_until:
            return CapabilityDecision(capability, "NOT_AVAILABLE", "retention period has expired")
        if capability in {"LLM", "SCRAPE"}:
            return CapabilityDecision(capability, "NOT_AVAILABLE", "external LLM and outbound scraping are not approved")
        if capability not in policy.approved_capabilities:
            return CapabilityDecision(capability, "NOT_ENTITLED", "capability is not approved for this source")
        if policy.data_mode == "LICENSED" and policy.rights_state != "APPROVED":
            return CapabilityDecision(capability, "NOT_ENTITLED", "licensed source has no approved rights state")
        if policy.data_mode == "SCRAPED_PUBLIC" and policy.rights_state != "APPROVED":
            return CapabilityDecision(capability, "NOT_ENTITLED", "public source rights are not approved")
        return CapabilityDecision(capability, "ALLOWED", "capability is approved")

    def require(self, policy: SourceCapabilityPolicy, capability: Capability, now: datetime | None = None) -> None:
        decision = self.decide(policy, capability, now)
        if decision.decision != "ALLOWED":
            raise CapabilityDenied(decision)


def source_is_disabled(policy: SourceCapabilityPolicy) -> bool:
    return not policy.enabled
