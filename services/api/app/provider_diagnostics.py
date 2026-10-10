"""Bounded, aggregate-only provider diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from app.external_provider_integrations import GatedReadOnlyProviderAdapter, SanitizedDiagnostic
from app.source_approval import SourceApprovalRecord


MAX_DIAGNOSTIC_REQUESTS = 6


@dataclass(frozen=True)
class DiagnosticPolicy:
    enabled: bool = False
    max_requests: int = MAX_DIAGNOSTIC_REQUESTS
    allow_raw_persistence: bool = False
    allow_model_training: bool = False

    def __post_init__(self) -> None:
        if self.max_requests < 1 or self.max_requests > MAX_DIAGNOSTIC_REQUESTS:
            raise ValueError("diagnostic request ceiling must be between 1 and 6")
        if self.allow_raw_persistence or self.allow_model_training:
            raise ValueError("diagnostic policy cannot enable raw persistence or model training")


class BoundedDiagnosticSession:
    """One-shot diagnostic session with no pagination, retry or raw retention."""

    def __init__(
        self,
        adapter: GatedReadOnlyProviderAdapter,
        *,
        approval: SourceApprovalRecord | Mapping[str, SourceApprovalRecord],
        code: str,
        policy: DiagnosticPolicy | None = None,
    ) -> None:
        self.adapter = adapter
        if isinstance(approval, Mapping):
            self.approvals = dict(approval)
        elif approval.approval_tier:
            self.approvals = {approval.approval_tier: approval}
        else:
            self.approvals = {}
        self.code = code
        self.policy = policy or DiagnosticPolicy()
        self._requests_used = 0

    @property
    def requests_used(self) -> int:
        return self._requests_used

    def run(
        self,
        operation: str,
        *,
        date: str | None = None,
        venue: str | None = None,
        race: int | None = None,
        view: str = "catalogue",
        cursor: str | None = None,
        page_size: int | None = None,
    ) -> SanitizedDiagnostic:
        if not self.policy.enabled:
            raise RuntimeError("provider diagnostics are disabled by the kill switch")
        if self._requests_used >= self.policy.max_requests:
            raise RuntimeError("diagnostic request ceiling reached")
        if cursor is not None or page_size is not None:
            raise ValueError("diagnostics do not permit pagination or caller-selected page sizes")
        if self._requests_used == 0 and operation != "ACCOUNT_METADATA_READ":
            raise ValueError("account metadata/quota check must be the first diagnostic request")
        tier = "ACCOUNT_METADATA_READ" if operation == "ACCOUNT_METADATA_READ" else "EPHEMERAL_READ_ONLY_DIAGNOSTIC"
        approval = self.approvals.get(tier)
        if approval is None:
            raise RuntimeError(f"missing distinct approval record for {tier}")
        self._requests_used += 1
        return self.adapter.diagnostic(
            operation,
            code=self.code,
            approval=approval,
            date=date,
            venue=venue,
            race=race,
            view=view,  # type: ignore[arg-type]
            request_ordinal=self._requests_used,
            request_ceiling=self.policy.max_requests,
        )
