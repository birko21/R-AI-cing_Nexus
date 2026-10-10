"""Prompt-injection, redaction, egress and tool-audit controls."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


DataMode = Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]
RightsState = Literal["SYNTHETIC", "UNASSESSED", "APPROVED", "RESTRICTED", "REJECTED"]
AuditEventType = Literal["TOOL_CALL", "TOOL_RESPONSE"]
EgressDestination = Literal["external_provider", "external_tool", "local_audit"]

_REDACTION_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("BEARER_TOKEN", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    ("SECRET_ASSIGNMENT", re.compile(r"(?i)\b(?:api[_ -]?key|token|secret|password)\s*[:=]\s*[^\s,;]+"), "[REDACTED_SECRET]"),
    ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    ("EMAIL", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE), "[REDACTED_EMAIL]"),
    ("PHONE", re.compile(r"(?<!\d)(?:\+?61\s?|0)4\d{2}[\s-]?\d{3}[\s-]?\d{3}(?!\d)"), "[REDACTED_PHONE]"),
)
_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("IGNORE_INSTRUCTIONS", re.compile(r"(?i)ignore\s+(?:all\s+)?(?:previous|prior|以上)\s+instructions")),
    ("ROLE_SPOOFING", re.compile(r"(?i)\b(?:system|developer)\s+(?:prompt|message|instruction)\b")),
    ("SECRET_REQUEST", re.compile(r"(?i)\b(?:reveal|show|print|dump)\s+(?:the\s+)?(?:system\s+prompt|secrets?|credentials?)\b")),
    ("TOOL_OVERRIDE", re.compile(r"(?i)\b(?:call|invoke|run)\s+(?:any|a|the)\s+tool\s+without\s+(?:approval|authorization)\b")),
)


class InjectionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    trusted: Literal[False] = False
    matched_rules: tuple[str, ...] = ()


class RedactionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str
    categories: tuple[str, ...] = ()
    original_sha256: str


class EgressRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1)
    destination: EgressDestination
    source_id: str = Field(min_length=1)
    text: str
    data_mode: DataMode
    rights_state: RightsState
    licensed_transmission_permitted: bool = False


class EgressDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str
    allowed: bool
    payload: str
    redaction_categories: tuple[str, ...]
    original_sha256: str
    reason: str


class ToolAuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str
    event_type: AuditEventType
    tool: str
    user_id: str
    occurred_at: datetime
    as_of: datetime
    limit: int
    argument_keys: tuple[str, ...] = ()
    status: str | None = None
    row_count: int | None = None


class ToolAuditLog:
    """In-memory append-only audit log that intentionally excludes raw data."""

    def __init__(self) -> None:
        self._events: list[ToolAuditEvent] = []

    def record_call(self, *, tool: str, user_id: str, as_of: datetime, limit: int, argument_keys: tuple[str, ...]) -> None:
        self._events.append(ToolAuditEvent(
            event_id=f"audit-{len(self._events) + 1}", event_type="TOOL_CALL", tool=tool, user_id=user_id,
            occurred_at=datetime.now(timezone.utc), as_of=as_of, limit=limit,
            argument_keys=tuple(sorted(argument_keys)),
        ))

    def record_response(self, *, tool: str, user_id: str, as_of: datetime, limit: int, status: str, row_count: int) -> None:
        self._events.append(ToolAuditEvent(
            event_id=f"audit-{len(self._events) + 1}", event_type="TOOL_RESPONSE", tool=tool, user_id=user_id,
            occurred_at=datetime.now(timezone.utc), as_of=as_of, limit=limit, status=status, row_count=row_count,
        ))

    def events(self) -> tuple[ToolAuditEvent, ...]:
        return tuple(self._events)


def assess_untrusted_text(text: str) -> InjectionAssessment:
    matched = tuple(rule for rule, pattern in _INJECTION_PATTERNS if pattern.search(text))
    return InjectionAssessment(matched_rules=matched)


def redact_text(text: str) -> RedactionResult:
    redacted = text
    categories: list[str] = []
    for category, pattern, replacement in _REDACTION_PATTERNS:
        if pattern.search(redacted):
            categories.append(category)
            redacted = pattern.sub(replacement, redacted)
    return RedactionResult(
        text=redacted,
        categories=tuple(categories),
        original_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def evaluate_egress(request: EgressRequest) -> EgressDecision:
    sanitized = redact_text(request.text)
    if request.rights_state in {"RESTRICTED", "REJECTED", "UNASSESSED"}:
        return EgressDecision(
            request_id=request.request_id, allowed=False, payload="", redaction_categories=sanitized.categories,
            original_sha256=sanitized.original_sha256, reason="rights state disallows transmission",
        )
    if request.data_mode == "LICENSED" and not request.licensed_transmission_permitted:
        return EgressDecision(
            request_id=request.request_id, allowed=False, payload="", redaction_categories=sanitized.categories,
            original_sha256=sanitized.original_sha256, reason="licensed-data transmission is not permitted",
        )
    return EgressDecision(
        request_id=request.request_id, allowed=True, payload=sanitized.text,
        redaction_categories=sanitized.categories, original_sha256=sanitized.original_sha256,
        reason="redacted payload permitted by rights policy",
    )


def audit_safe_json(events: tuple[ToolAuditEvent, ...]) -> str:
    """Serialize audit metadata only; used by evidence fixtures and inspections."""

    return json.dumps([event.model_dump(mode="json") for event in events], sort_keys=True)
