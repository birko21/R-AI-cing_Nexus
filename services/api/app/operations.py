"""Local observability, quota, cost and provider kill-switch controls."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AlertLevel = Literal["NONE", "WARN_50", "WARN_80", "CAP_100"]


class UsageEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    job_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    started_at: datetime
    latency_ms: int = Field(ge=0)
    status: Literal["SUCCESS", "ERROR"]
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_spend_aud: Decimal = Field(ge=0)
    critical: bool = False

    @model_validator(mode="after")
    def require_timezone(self) -> UsageEvent:
        if self.started_at.tzinfo is None or self.started_at.utcoffset() is None:
            raise ValueError("started_at must be timezone-aware")
        return self


@dataclass(frozen=True)
class BudgetConfig:
    daily_spend_aud: Decimal = Decimal("1.00")
    daily_tokens: int = 10000

    def __post_init__(self) -> None:
        if self.daily_spend_aud <= 0 or self.daily_tokens <= 0:
            raise ValueError("budget limits must be positive")


class OperationsLedger:
    def __init__(self, config: BudgetConfig) -> None:
        self.config = config
        self._events: list[UsageEvent] = []
        self._disabled_providers: set[str] = set()

    def record(self, event: UsageEvent) -> None:
        self._events.append(event)

    def events(self) -> tuple[UsageEvent, ...]:
        return tuple(self._events)

    def disable_provider(self, provider: str) -> None:
        self._disabled_providers.add(provider)

    def enable_provider(self, provider: str) -> None:
        self._disabled_providers.discard(provider)

    def snapshot(self) -> dict[str, object]:
        spend = sum((event.estimated_spend_aud for event in self._events), Decimal("0"))
        tokens = sum(event.input_tokens + event.output_tokens for event in self._events)
        ratio = max(spend / self.config.daily_spend_aud, Decimal(tokens) / Decimal(self.config.daily_tokens))
        level: AlertLevel = "CAP_100" if ratio >= 1 else "WARN_80" if ratio >= Decimal("0.8") else "WARN_50" if ratio >= Decimal("0.5") else "NONE"
        return {
            "jobs": len(self._events), "errors": sum(event.status == "ERROR" for event in self._events),
            "latency_ms_avg": (sum(event.latency_ms for event in self._events) / len(self._events)) if self._events else 0,
            "input_tokens": sum(event.input_tokens for event in self._events), "output_tokens": sum(event.output_tokens for event in self._events),
            "estimated_spend_aud": str(spend), "budget_ratio": str(ratio), "alert_level": level,
            "noncritical_outbound_enabled": level != "CAP_100", "disabled_providers": sorted(self._disabled_providers),
        }

    def outbound_allowed(self, provider: str, *, critical: bool) -> bool:
        snapshot = self.snapshot()
        return provider not in self._disabled_providers and (critical or bool(snapshot["noncritical_outbound_enabled"]))
