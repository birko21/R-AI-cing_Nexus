"""Approval gate and unavailable stub for a first real provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ApprovalStatus = Literal["APPROVED", "BLOCKED_EXTERNAL_DEPENDENCY"]
ApprovalTier = Literal[
    "ACCOUNT_METADATA_READ",
    "EPHEMERAL_READ_ONLY_DIAGNOSTIC",
    "PRIVATE_SINGLE_OWNER_READ_ONLY",
    "HISTORICAL_RETENTION_AND_MODEL_TRAINING",
]

REQUIRED_APPROVALS = (
    "written_rights",
    "credential_policy",
    "retention_terms",
    "model_training_permission",
    "display_permission",
    "reconciliation_report",
)


@dataclass(frozen=True)
class SourceApprovalRecord:
    source_id: str
    written_rights: str | None = None
    credential_policy: str | None = None
    retention_terms: str | None = None
    model_training_permission: str | None = None
    display_permission: str | None = None
    reconciliation_report: str | None = None
    approved_operations: tuple[str, ...] = ()
    approved_codes: tuple[str, ...] = ()
    approval_tier: ApprovalTier | None = None
    account_entitlement_evidence: str | None = None
    credential_custodian: str | None = None
    quota_ceiling: str | None = None
    kill_switch_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id is required")

    def missing_requirements(self) -> tuple[str, ...]:
        return tuple(name for name in REQUIRED_APPROVALS if not getattr(self, name))


TIER_REQUIREMENTS = (
    "account_entitlement_evidence",
    "credential_custodian",
    "quota_ceiling",
    "kill_switch_reference",
)


def evaluate_tiered_source_approval(
    record: SourceApprovalRecord,
    *,
    required_tier: ApprovalTier,
    operation: str,
    code: str,
) -> SourceCheckpoint:
    """Evaluate a narrowly scoped approval without inferring stronger rights."""

    missing = [name for name in TIER_REQUIREMENTS if not getattr(record, name)]
    if record.approval_tier != required_tier:
        missing.append("approval_tier")
    if operation not in record.approved_operations:
        missing.append("approved_operations")
    if code not in record.approved_codes:
        missing.append("approved_codes")
    if required_tier == "HISTORICAL_RETENTION_AND_MODEL_TRAINING":
        missing.extend(name for name in record.missing_requirements() if name not in missing)
    if missing:
        return SourceCheckpoint(
            record.source_id,
            "BLOCKED_EXTERNAL_DEPENDENCY",
            tuple(missing),
            "The named approval tier does not authorize this operation and racing code.",
        )
    return SourceCheckpoint(record.source_id, "APPROVED", (), "The exact approval tier, operation and racing code are recorded.")


@dataclass(frozen=True)
class SourceCheckpoint:
    source_id: str
    status: ApprovalStatus
    missing_requirements: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "missing_requirements": list(self.missing_requirements),
            "reason": self.reason,
        }


def evaluate_source_approval(record: SourceApprovalRecord) -> SourceCheckpoint:
    missing = record.missing_requirements()
    if missing:
        return SourceCheckpoint(
            record.source_id,
            "BLOCKED_EXTERNAL_DEPENDENCY",
            missing,
            "Written source rights, credential policy, retention, model-use, display and reconciliation evidence are incomplete.",
        )
    return SourceCheckpoint(record.source_id, "APPROVED", (), "All required source evidence is recorded.")


class UnavailableSourceStub:
    """Explicitly non-fetching interface used until a source is approved."""

    def __init__(self, checkpoint: SourceCheckpoint) -> None:
        if checkpoint.status != "BLOCKED_EXTERNAL_DEPENDENCY":
            raise ValueError("unavailable stub requires a blocked source checkpoint")
        self.checkpoint = checkpoint

    def request(self, operation: str) -> dict[str, object]:
        return {
            "status": "NOT_AVAILABLE",
            "operation": operation,
            "source_id": self.checkpoint.source_id,
            "reason": self.checkpoint.reason,
            "checkpoint": self.checkpoint.status,
        }
