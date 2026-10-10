"""Bounded, read-only research tool contracts with ACL and as-of enforcement."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.egress import ToolAuditLog


ToolName = Literal["races", "histories", "features", "markets", "forecasts", "backtests", "provenance"]
ToolStatus = Literal["OK", "NOT_AVAILABLE", "NOT_ENTITLED"]

TOOL_SCOPES: dict[str, str] = {
    "races": "races:read", "histories": "races:read", "features": "forecasts:read",
    "markets": "markets:read", "forecasts": "forecasts:read", "backtests": "backtests:read", "provenance": "provenance:read",
}


class ResearchToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool: ToolName
    user_id: str = Field(min_length=1)
    as_of: datetime
    limit: int = Field(default=25, ge=1, le=100)
    arguments: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_timezone(self) -> ResearchToolRequest:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        return self


class ResearchToolResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool: ToolName
    status: ToolStatus
    as_of: datetime
    rows: list[dict[str, object]]
    limit: int
    reason: str
    read_only: Literal[True] = True


ToolHandler = Callable[[datetime, int, Mapping[str, object]], list[dict[str, object]]]


class ResearchToolRegistry:
    def __init__(self, audit_log: ToolAuditLog | None = None) -> None:
        self._handlers: dict[str, ToolHandler] = {}
        self._audit_log = audit_log

    def register(self, tool: ToolName, handler: ToolHandler) -> None:
        self._handlers[tool] = handler

    def catalog(self) -> list[dict[str, object]]:
        return [
            {"tool": tool, "required_scope": TOOL_SCOPES[tool], "read_only": True, "requires_as_of": True, "max_rows": 100}
            for tool in TOOL_SCOPES
        ]

    def execute(self, request: ResearchToolRequest, *, scopes: set[str]) -> ResearchToolResponse:
        if self._audit_log is not None:
            self._audit_log.record_call(
                tool=request.tool, user_id=request.user_id, as_of=request.as_of,
                limit=request.limit, argument_keys=tuple(request.arguments),
            )
        required_scope = TOOL_SCOPES[request.tool]
        if required_scope not in scopes:
            response = ResearchToolResponse(tool=request.tool, status="NOT_ENTITLED", as_of=request.as_of, rows=[], limit=request.limit, reason=f"required scope {required_scope} is missing")
            self._audit_response(request, response)
            return response
        handler = self._handlers.get(request.tool)
        if handler is None:
            response = ResearchToolResponse(tool=request.tool, status="NOT_AVAILABLE", as_of=request.as_of, rows=[], limit=request.limit, reason="tool capability is not available")
            self._audit_response(request, response)
            return response
        rows = handler(request.as_of, request.limit, request.arguments)[:request.limit]
        response = ResearchToolResponse(tool=request.tool, status="OK", as_of=request.as_of, rows=rows, limit=request.limit, reason="bounded read-only result")
        self._audit_response(request, response)
        return response

    def _audit_response(self, request: ResearchToolRequest, response: ResearchToolResponse) -> None:
        if self._audit_log is not None:
            self._audit_log.record_response(
                tool=request.tool, user_id=request.user_id, as_of=request.as_of,
                limit=request.limit, status=response.status, row_count=len(response.rows),
            )
