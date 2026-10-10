"""Evidence-backed claim contracts that fail closed on unsupported assertions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ClaimType = Literal["FACT", "PROBABILITY", "CURRENTNESS", "SOURCE_ASSERTION"]
DataMode = Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]


class EvidenceClaim(BaseModel):
    """A factual claim with the evidence needed to display it safely.

    The explicit verification switches prevent metadata alone from becoming a
    claim that a probability is supported, a source is official/licensed, or
    data is current.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str = Field(min_length=1)
    claim_type: ClaimType
    text: str = Field(min_length=1, max_length=4000)
    source_ids: tuple[str, ...] = Field(min_length=1)
    model_ids: tuple[str, ...] = Field(min_length=1)
    observed_at: datetime
    limitations: tuple[str, ...] = Field(min_length=1)
    data_mode: DataMode
    numeric_value: float | None = None
    probability_supported: bool = False
    currentness_verified: bool = False
    source_assertion_verified: bool = False

    @model_validator(mode="after")
    def validate_evidence(self) -> EvidenceClaim:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        if any(not value.strip() for value in (*self.source_ids, *self.model_ids, *self.limitations)):
            raise ValueError("source_ids, model_ids and limitations must contain non-empty values")
        if self.claim_type == "PROBABILITY":
            if self.numeric_value is None or not 0 <= self.numeric_value <= 1:
                raise ValueError("probability claims require numeric_value between 0 and 1")
            if not self.probability_supported:
                raise ValueError("probability claim lacks supporting evidence")
        elif self.numeric_value is not None:
            raise ValueError("numeric_value is only valid for probability claims")
        if self.claim_type == "CURRENTNESS" and not self.currentness_verified:
            raise ValueError("currentness claim lacks a freshness verification record")
        if self.claim_type == "SOURCE_ASSERTION" and not self.source_assertion_verified:
            raise ValueError("source assertion lacks rights or provenance evidence")
        return self


def validate_claim(payload: EvidenceClaim | dict[str, object]) -> EvidenceClaim:
    """Parse and validate a claim, raising on unsupported assertions."""

    if isinstance(payload, EvidenceClaim):
        return payload
    return EvidenceClaim.model_validate(payload)
