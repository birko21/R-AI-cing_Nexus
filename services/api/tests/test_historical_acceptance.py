from datetime import datetime, timedelta, timezone

from app.historical_acceptance import HistoricalReceipt, validate_historical_receipts


UTC = timezone.utc


def receipt(*, value: str = "r1", receipt_id: str | None = None, rights: str = "APPROVED", observed_offset: int = -120) -> HistoricalReceipt:
    start = datetime(2026, 1, 15, 1, tzinfo=UTC)
    return HistoricalReceipt(
        "PuntersEdge", "THOROUGHBRED", "race-1", "runner-1", start,
        start + timedelta(seconds=observed_offset), start + timedelta(seconds=observed_offset + 10),
        start + timedelta(seconds=observed_offset + 20), receipt_id or value, "a" * 64, rights,
    )


def test_acceptance_requires_approved_rights_and_pre_race_timestamps() -> None:
    report = validate_historical_receipts((receipt(),))
    assert report.status == "ACCEPTED_FOR_OFFLINE_INGESTION"
    assert report.accepted_receipt_count == 1
    rejected = validate_historical_receipts((receipt(rights="PERSONAL_ONLY"), receipt(value="r2", observed_offset=5)))
    assert rejected.status == "REJECTED_PENDING_RECONCILIATION"
    assert {issue.reason for issue in rejected.issues} == {"RIGHTS_NOT_APPROVED", "OBSERVATION_NOT_PRE_RACE"}


def test_acceptance_rejects_duplicate_provider_runner_identity() -> None:
    report = validate_historical_receipts((receipt(), receipt(receipt_id="r2")))
    assert report.status == "REJECTED_PENDING_RECONCILIATION"
    assert report.issues[0].reason == "DUPLICATE_PROVIDER_RUNNER"
