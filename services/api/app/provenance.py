from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain import DomainInvariantError


DataMode = Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]
RightsState = Literal["SYNTHETIC", "UNASSESSED", "APPROVED", "RESTRICTED", "REJECTED"]
QuarantineReason = Literal[
    "CHECKSUM_MISMATCH",
    "INVALID_SCHEMA",
    "MISSING_SOURCE_ID",
    "UNRESOLVED_IDENTITY",
    "RIGHTS_UNASSESSED",
    "PARSE_ERROR",
]


def payload_sha256(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class RawEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    envelope_id: str = Field(min_length=1)
    source_identifier: str = Field(min_length=1)
    payload: dict[str, object]
    payload_sha256: str = Field(min_length=64, max_length=64)
    schema_version: str = Field(min_length=1)
    retrieved_at: datetime
    first_observed_at: datetime
    published_at: datetime | None = None
    data_mode: DataMode
    rights_state: RightsState
    licence_reference: str | None = None
    retrieval_metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_receipt(self):
        for field_name in ("retrieved_at", "first_observed_at", "published_at"):
            value = getattr(self, field_name)
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise DomainInvariantError(f"{field_name} must be timezone-aware")
        if self.payload_sha256 != payload_sha256(self.payload):
            raise DomainInvariantError("payload checksum does not match canonical payload")
        if self.data_mode == "SYNTHETIC_ONLY" and self.rights_state != "SYNTHETIC":
            raise DomainInvariantError("synthetic envelopes require SYNTHETIC rights state")
        if self.data_mode == "LICENSED" and not self.licence_reference:
            raise DomainInvariantError("licensed envelopes require a licence reference")
        return self


class QuarantineRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    quarantine_id: str = Field(default_factory=lambda: str(uuid4()))
    envelope_id: str
    reason_code: QuarantineReason
    detail: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IngestResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    envelope: RawEnvelope | None = None
    quarantine: QuarantineRecord | None = None


def ingest_raw_envelope(raw: dict[str, object]) -> IngestResult:
    envelope_id = str(raw.get("envelope_id") or "unidentified")
    if not str(raw.get("source_identifier") or "").strip():
        return IngestResult(
            quarantine=QuarantineRecord(
                envelope_id=envelope_id,
                reason_code="MISSING_SOURCE_ID",
                detail="source_identifier is required",
            )
        )
    try:
        return IngestResult(envelope=RawEnvelope.model_validate(raw))
    except DomainInvariantError as exc:
        reason = "CHECKSUM_MISMATCH" if "checksum" in str(exc) else "RIGHTS_UNASSESSED"
        return IngestResult(
            quarantine=QuarantineRecord(envelope_id=envelope_id, reason_code=reason, detail=str(exc))
        )
    except Exception as exc:
        detail = str(exc)
        lowered = detail.lower()
        if "checksum" in lowered:
            reason = "CHECKSUM_MISMATCH"
        elif "licence" in lowered or "rights" in lowered:
            reason = "RIGHTS_UNASSESSED"
        else:
            reason = "INVALID_SCHEMA"
        return IngestResult(
            quarantine=QuarantineRecord(envelope_id=envelope_id, reason_code=reason, detail=detail)
        )
