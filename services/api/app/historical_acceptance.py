"""Offline acceptance checks for an owner-approved historical data sample."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib


@dataclass(frozen=True)
class HistoricalReceipt:
    provider: str
    code: str
    provider_race_id: str
    provider_runner_id: str
    race_start_at: datetime
    observed_at: datetime | None
    published_at: datetime | None
    retrieved_at: datetime
    source_receipt_id: str
    payload_sha256: str
    rights_state: str
    identity_evidence: str = "EXACT"


@dataclass(frozen=True)
class AcceptanceIssue:
    receipt_id: str
    reason: str
    severity: str


@dataclass(frozen=True)
class HistoricalAcceptanceReport:
    status: str
    receipt_count: int
    accepted_receipt_count: int
    dataset_hash: str
    issues: tuple[AcceptanceIssue, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "receipt_count": self.receipt_count,
            "accepted_receipt_count": self.accepted_receipt_count,
            "dataset_hash": self.dataset_hash,
            "issues": [asdict(issue) for issue in self.issues],
        }


def _aware(value: datetime | None) -> bool:
    return value is not None and value.tzinfo is not None and value.utcoffset() is not None


def validate_historical_receipts(receipts: tuple[HistoricalReceipt, ...], *, approved_codes: frozenset[str] = frozenset({"THOROUGHBRED"})) -> HistoricalAcceptanceReport:
    """Validate receipts without network access or provider-specific assumptions."""

    issues: list[AcceptanceIssue] = []
    seen_receipts: set[str] = set()
    seen_runner_keys: set[tuple[str, str, str, str]] = set()
    accepted: list[HistoricalReceipt] = []
    for receipt in receipts:
        receipt_id = receipt.source_receipt_id or "UNKNOWN"
        if receipt_id in seen_receipts:
            issues.append(AcceptanceIssue(receipt_id, "DUPLICATE_RECEIPT_ID", "ERROR"))
            continue
        seen_receipts.add(receipt_id)
        required_times = (receipt.race_start_at, receipt.retrieved_at)
        if not all(_aware(value) for value in required_times) or (receipt.observed_at is not None and not _aware(receipt.observed_at)) or (receipt.published_at is not None and not _aware(receipt.published_at)):
            issues.append(AcceptanceIssue(receipt_id, "MISSING_OR_NAIVE_TIMESTAMP", "ERROR"))
            continue
        if receipt.observed_at is not None and receipt.observed_at >= receipt.race_start_at:
            issues.append(AcceptanceIssue(receipt_id, "OBSERVATION_NOT_PRE_RACE", "ERROR"))
            continue
        if receipt.published_at is not None and receipt.published_at >= receipt.race_start_at:
            issues.append(AcceptanceIssue(receipt_id, "PUBLICATION_NOT_PRE_RACE", "ERROR"))
            continue
        if receipt.retrieved_at >= receipt.race_start_at:
            issues.append(AcceptanceIssue(receipt_id, "RETRIEVAL_NOT_PRE_RACE", "ERROR"))
            continue
        if receipt.code not in approved_codes:
            issues.append(AcceptanceIssue(receipt_id, "CODE_NOT_IN_APPROVED_SAMPLE", "ERROR"))
            continue
        if receipt.rights_state != "APPROVED":
            issues.append(AcceptanceIssue(receipt_id, "RIGHTS_NOT_APPROVED", "ERROR"))
            continue
        if receipt.identity_evidence not in {"EXACT", "RECONCILED"}:
            issues.append(AcceptanceIssue(receipt_id, "IDENTITY_EVIDENCE_INSUFFICIENT", "ERROR"))
            continue
        if len(receipt.payload_sha256) != 64 or any(character not in "0123456789abcdef" for character in receipt.payload_sha256.lower()):
            issues.append(AcceptanceIssue(receipt_id, "PAYLOAD_HASH_INVALID", "ERROR"))
            continue
        runner_key = (receipt.provider, receipt.code, receipt.provider_race_id, receipt.provider_runner_id)
        if runner_key in seen_runner_keys:
            issues.append(AcceptanceIssue(receipt_id, "DUPLICATE_PROVIDER_RUNNER", "ERROR"))
            continue
        seen_runner_keys.add(runner_key)
        accepted.append(receipt)
    digest_input = [{key: str(value) for key, value in asdict(receipt).items() if key not in {"observed_at", "published_at", "retrieved_at", "race_start_at"}} for receipt in accepted]
    dataset_hash = hashlib.sha256(repr(sorted(digest_input, key=lambda value: (value["provider"], value["provider_race_id"], value["provider_runner_id"]))).encode("utf-8")).hexdigest()
    status = "ACCEPTED_FOR_OFFLINE_INGESTION" if accepted and not issues else "REJECTED_PENDING_RECONCILIATION"
    return HistoricalAcceptanceReport(status, len(receipts), len(accepted), dataset_hash, tuple(issues))
