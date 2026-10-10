from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain import DomainInvariantError
from app.temporal import BitemporalFact, select_as_of


def fact(
    revision: str,
    value: str,
    observed_day: int,
    valid_from_day: int,
    *,
    proof: bool = True,
    published_day: int | None = None,
) -> BitemporalFact:
    return BitemporalFact(
        fact_revision_id=revision,
        fact_key="race-1.status",
        source_event_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        published_at=(datetime(2026, 1, published_day, tzinfo=timezone.utc) if published_day else None),
        observed_at=datetime(2026, 1, observed_day, tzinfo=timezone.utc),
        effective_from=datetime(2026, 1, valid_from_day, tzinfo=timezone.utc),
        source_receipt_id="receipt-1",
        receipt_proof=proof,
        system_valid_from=datetime(2026, 1, observed_day, tzinfo=timezone.utc),
        payload={"status": value},
    )


def test_as_of_snapshot_excludes_future_observations_and_keeps_old_revision() -> None:
    original = fact("r1", "FINAL_FIELDS", 2, 2, published_day=2)
    correction = fact("r2", "OFFICIAL", 5, 5, published_day=5)

    before_correction = select_as_of([original, correction], datetime(2026, 1, 4, tzinfo=timezone.utc))
    after_correction = select_as_of([original, correction], datetime(2026, 1, 6, tzinfo=timezone.utc))

    assert before_correction[0].payload["status"] == "FINAL_FIELDS"
    assert after_correction[0].payload["status"] == "OFFICIAL"


def test_missing_receipt_proof_is_excluded() -> None:
    unverified = fact("r1", "FINAL_FIELDS", 2, 2, proof=False)
    assert select_as_of([unverified], datetime(2026, 1, 3, tzinfo=timezone.utc)) == []


def test_naive_time_and_invalid_intervals_are_rejected() -> None:
    with pytest.raises((DomainInvariantError, ValidationError), match="timezone-aware"):
        select_as_of(
            [fact("r1", "FINAL_FIELDS", 2, 2).model_copy(update={"observed_at": datetime(2026, 1, 2)})],
            datetime(2026, 1, 3, tzinfo=timezone.utc),
        )
    with pytest.raises(ValidationError, match="published_at"):
        BitemporalFact(
            fact_revision_id="r1",
            fact_key="race-1.status",
            source_event_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            observed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            effective_from=datetime(2026, 1, 2, tzinfo=timezone.utc),
            system_valid_from=datetime(2026, 1, 2, tzinfo=timezone.utc),
            source_receipt_id="receipt-1",
            receipt_proof=True,
        )
