from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.evidence import EvidenceClaim, validate_claim


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "claim_id": "claim-1",
        "claim_type": "FACT",
        "text": "The synthetic fixture contains six races.",
        "source_ids": ("fixture:synthetic-v1",),
        "model_ids": ("B0_UNIFORM",),
        "observed_at": NOW,
        "limitations": ("Synthetic implementation evidence; not a live racing fact.",),
        "data_mode": "SYNTHETIC_ONLY",
    }
    payload.update(overrides)
    return payload


def test_factual_claim_requires_immutable_evidence_metadata() -> None:
    claim = validate_claim(evidence())
    assert claim.source_ids == ("fixture:synthetic-v1",)
    assert claim.model_ids == ("B0_UNIFORM",)
    assert claim.observed_at == NOW
    assert claim.limitations


@pytest.mark.parametrize(
    ("claim_type", "overrides", "message"),
    [
        ("PROBABILITY", {"numeric_value": 0.42}, "supporting evidence"),
        ("PROBABILITY", {"numeric_value": 1.1, "probability_supported": True}, "between 0 and 1"),
        ("CURRENTNESS", {}, "freshness verification"),
        ("SOURCE_ASSERTION", {}, "rights or provenance"),
    ],
)
def test_unsupported_numeric_currentness_and_source_claims_are_rejected(
    claim_type: str, overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        EvidenceClaim.model_validate(evidence(claim_type=claim_type, **overrides))


def test_supported_probability_and_verified_assertions_are_accepted() -> None:
    probability = validate_claim(evidence(claim_type="PROBABILITY", numeric_value=0.42, probability_supported=True))
    current = validate_claim(evidence(claim_type="CURRENTNESS", currentness_verified=True))
    source = validate_claim(evidence(claim_type="SOURCE_ASSERTION", source_assertion_verified=True))
    assert probability.numeric_value == 0.42
    assert current.claim_type == "CURRENTNESS"
    assert source.claim_type == "SOURCE_ASSERTION"


def test_claim_rejects_naive_timestamp_and_missing_required_metadata() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        EvidenceClaim.model_validate(evidence(observed_at=datetime(2026, 1, 15)))
    with pytest.raises(ValidationError):
        EvidenceClaim.model_validate(evidence(source_ids=()))
    with pytest.raises(ValidationError):
        EvidenceClaim.model_validate(evidence(model_ids=()))
    with pytest.raises(ValidationError):
        EvidenceClaim.model_validate(evidence(limitations=()))
