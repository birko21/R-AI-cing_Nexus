"""Immutable provenance, retention and replay for public scraped records."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Literal
from urllib.parse import urlparse

from app.provenance import RawEnvelope, payload_sha256


RetentionStatus = Literal["ACTIVE", "EXPIRED"]
ReplayParser = Callable[[bytes], dict[str, object]]


class ScrapedProvenanceError(ValueError):
    """Raised when a scraped receipt cannot be stored or replayed safely."""


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ScrapedProvenanceError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True)
class ReplayFixture:
    fixture_id: str
    content: str
    content_sha256: str
    parser_version: str

    def __post_init__(self) -> None:
        if not self.fixture_id.strip() or not self.parser_version.strip():
            raise ScrapedProvenanceError("replay fixture identity and parser version are required")
        actual = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        if self.content_sha256 != actual:
            raise ScrapedProvenanceError("replay fixture content checksum does not match")

    @classmethod
    def from_payload(cls, fixture_id: str, payload: dict[str, object], parser_version: str) -> ReplayFixture:
        content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        return cls(fixture_id, content, hashlib.sha256(content.encode("utf-8")).hexdigest(), parser_version)

    def to_dict(self) -> dict[str, object]:
        return {
            "fixture_id": self.fixture_id,
            "content": self.content,
            "content_sha256": self.content_sha256,
            "parser_version": self.parser_version,
        }


@dataclass(frozen=True)
class ScrapedSourceReceipt:
    receipt_id: str
    envelope: RawEnvelope
    retrieval_url: str
    retrieved_at: datetime
    content_sha256: str
    parser_version: str
    replay_fixture_id: str
    retention_until: datetime | None = None

    def __post_init__(self) -> None:
        parsed = urlparse(self.retrieval_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ScrapedProvenanceError("scraped receipts require credential-free HTTPS URLs")
        if not self.receipt_id.strip() or not self.parser_version.strip() or not self.replay_fixture_id.strip():
            raise ScrapedProvenanceError("receipt identity, parser version and replay fixture are required")
        if len(self.content_sha256) != 64:
            raise ScrapedProvenanceError("content_sha256 must be a SHA-256 digest")
        _require_utc(self.retrieved_at, "retrieved_at")
        _require_utc(self.envelope.retrieved_at, "envelope.retrieved_at")
        if self.envelope.data_mode != "SCRAPED_PUBLIC":
            raise ScrapedProvenanceError("scraped receipts must use SCRAPED_PUBLIC data mode")
        if self.envelope.retrieved_at != self.retrieved_at:
            raise ScrapedProvenanceError("receipt and envelope retrieval timestamps must match")
        if self.retention_until is not None:
            _require_utc(self.retention_until, "retention_until")

    def retention_status(self, now: datetime) -> RetentionStatus:
        _require_utc(now, "now")
        if self.retention_until is not None and now.astimezone(timezone.utc) >= self.retention_until.astimezone(timezone.utc):
            return "EXPIRED"
        return "ACTIVE"

    def provenance_view(self, now: datetime) -> dict[str, object]:
        return {
            "receipt_id": self.receipt_id,
            "retrieval_url": self.retrieval_url,
            "retrieved_at": self.retrieved_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "content_sha256": self.content_sha256,
            "parser_version": self.parser_version,
            "data_mode": self.envelope.data_mode,
            "rights_state": self.envelope.rights_state,
            "retention_status": self.retention_status(now),
            "retention_until": self.retention_until.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if self.retention_until else None,
            "replay_fixture_id": self.replay_fixture_id,
            "licensed": False,
            "official": False,
        }


class ScrapedProvenanceStore:
    """Append-only receipt/fixture store used by local ingestion and replay."""

    def __init__(self) -> None:
        self._receipts: dict[str, ScrapedSourceReceipt] = {}
        self._fixtures: dict[str, ReplayFixture] = {}

    def append(self, receipt: ScrapedSourceReceipt, fixture: ReplayFixture) -> None:
        if receipt.receipt_id in self._receipts or fixture.fixture_id in self._fixtures:
            raise ScrapedProvenanceError("scraped receipts and replay fixtures are append-only")
        if receipt.replay_fixture_id != fixture.fixture_id:
            raise ScrapedProvenanceError("receipt does not reference the supplied replay fixture")
        if receipt.parser_version != fixture.parser_version:
            raise ScrapedProvenanceError("receipt parser version does not match replay fixture")
        self._receipts[receipt.receipt_id] = receipt
        self._fixtures[fixture.fixture_id] = fixture

    def get(self, receipt_id: str) -> ScrapedSourceReceipt:
        try:
            return self._receipts[receipt_id]
        except KeyError as exc:
            raise ScrapedProvenanceError("scraped receipt was not found") from exc

    def provenance_view(self, receipt_id: str, now: datetime) -> dict[str, object]:
        return self.get(receipt_id).provenance_view(now)

    def replay(self, receipt_id: str, parser: ReplayParser, now: datetime) -> dict[str, object]:
        receipt = self.get(receipt_id)
        if receipt.retention_status(now) != "ACTIVE":
            raise ScrapedProvenanceError("scraped replay is unavailable after retention expiry")
        fixture = self._fixtures[receipt.replay_fixture_id]
        if fixture.content_sha256 != receipt.content_sha256:
            raise ScrapedProvenanceError("replay fixture does not match receipt content hash")
        parsed = parser(fixture.content.encode("utf-8"))
        if parsed != receipt.envelope.payload:
            raise ScrapedProvenanceError("replay output does not match the stored raw envelope")
        if payload_sha256(parsed) != receipt.envelope.payload_sha256:
            raise ScrapedProvenanceError("replay output checksum does not match the stored envelope")
        return parsed
