"""Rights-aware market quote and exact runner-mapping contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain import VALID_CODES, DomainInvariantError, MarketSelectionMapping


PriceType = Literal["DECIMAL", "FRACTIONAL", "AMERICAN", "TOTAL_RETURN"]
MarketType = Literal["WIN", "PLACE", "TOP_N", "HEAD_TO_HEAD"]
PricePhase = Literal["LIVE", "CLOSING"]
QuoteSide = Literal["BACK", "LAY"]
RunnerStatus = Literal["ACTIVE", "SCRATCHED", "RESERVE"]
DataMode = Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]
RightsState = Literal["SYNTHETIC", "UNASSESSED", "APPROVED", "RESTRICTED", "REJECTED"]
QuarantineReason = Literal["MISSING_EXACT_MAPPING", "INVALID_MAPPING", "INVALID_QUOTE"]


class MarketQuote(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    quote_id: str = Field(min_length=1)
    mapping: MarketSelectionMapping
    market_type: MarketType
    price_type: PriceType
    price_phase: PricePhase = "LIVE"
    quote_side: QuoteSide = "BACK"
    runner_status: RunnerStatus = "ACTIVE"
    price: float
    source_timestamp: datetime
    retrieved_at: datetime
    in_play: bool
    size: float | None = Field(default=None, gt=0)
    liquidity: float | None = Field(default=None, gt=0)
    entitlement_reference: str = Field(min_length=1)
    source_receipt_id: str = Field(min_length=1)
    data_mode: DataMode
    rights_state: RightsState

    @model_validator(mode="after")
    def validate_quote(self) -> MarketQuote:
        if self.mapping.code not in VALID_CODES:
            raise DomainInvariantError("quote mapping uses an unsupported racing code")
        for field_name in ("source_timestamp", "retrieved_at"):
            timestamp = getattr(self, field_name)
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise DomainInvariantError(f"{field_name} must be timezone-aware")
        if self.source_timestamp > self.retrieved_at:
            raise DomainInvariantError("source timestamp cannot be after retrieval timestamp")
        if self.price_type == "DECIMAL" and self.price < 1:
            raise DomainInvariantError("decimal price must be at least 1")
        if self.price_type in {"FRACTIONAL", "TOTAL_RETURN"} and self.price <= 0:
            raise DomainInvariantError("fractional and total-return prices must be positive")
        if self.price_type == "AMERICAN" and self.price == 0:
            raise DomainInvariantError("american price cannot be zero")
        if self.data_mode == "SYNTHETIC_ONLY" and self.rights_state != "SYNTHETIC":
            raise DomainInvariantError("synthetic quotes require SYNTHETIC rights state")
        if self.data_mode == "LICENSED" and self.rights_state != "APPROVED":
            raise DomainInvariantError("licensed quotes require approved rights")
        return self


class QuoteQuarantine(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    quote_id: str
    reason_code: QuarantineReason
    detail: str


class QuoteIngestResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    quote: MarketQuote | None = None
    quarantine: QuoteQuarantine | None = None


EXACT_MAPPING_FIELDS = ("code", "race_id", "field_revision", "entry_id", "market_source", "market_id", "selection_id")


def ingest_market_quote(raw: Mapping[str, object]) -> QuoteIngestResult:
    quote_id = str(raw.get("quote_id") or "unidentified")
    mapping = raw.get("mapping")
    if not isinstance(mapping, Mapping) or any(not str(mapping.get(field) or "").strip() for field in EXACT_MAPPING_FIELDS):
        return QuoteIngestResult(
            quarantine=QuoteQuarantine(
                quote_id=quote_id,
                reason_code="MISSING_EXACT_MAPPING",
                detail="quote requires exact code, race, field revision, entry, market and selection identifiers",
            )
        )
    try:
        return QuoteIngestResult(quote=MarketQuote.model_validate(dict(raw)))
    except (DomainInvariantError, ValueError, TypeError) as exc:
        reason: QuarantineReason = "INVALID_MAPPING" if "mapping" in str(exc).lower() else "INVALID_QUOTE"
        return QuoteIngestResult(quarantine=QuoteQuarantine(quote_id=quote_id, reason_code=reason, detail=str(exc)))
