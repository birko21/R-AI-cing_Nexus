from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.research_tools import ResearchToolRegistry, ResearchToolRequest


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def test_catalog_declares_bounded_read_only_tools_and_as_of() -> None:
    catalog = ResearchToolRegistry().catalog()
    assert {item["tool"] for item in catalog} == {"races", "histories", "features", "markets", "forecasts", "backtests", "provenance"}
    assert all(item["read_only"] and item["requires_as_of"] and item["max_rows"] == 100 for item in catalog)


def test_authorized_tool_is_bounded_and_receives_as_of() -> None:
    registry = ResearchToolRegistry()
    observed: list[tuple[datetime, int, dict[str, object]]] = []

    def handler(as_of: datetime, limit: int, arguments: dict[str, object]) -> list[dict[str, object]]:
        observed.append((as_of, limit, arguments))
        return [{"id": str(index)} for index in range(150)]

    registry.register("races", handler)
    request = ResearchToolRequest(tool="races", user_id="owner", as_of=NOW, limit=100, arguments={"code": "THOROUGHBRED"})
    response = registry.execute(request, scopes={"races:read"})
    assert response.status == "OK"
    assert len(response.rows) == 100
    assert observed == [(NOW, 100, {"code": "THOROUGHBRED"})]


def test_missing_scope_and_unavailable_tool_fail_closed() -> None:
    registry = ResearchToolRegistry()
    not_entitled = registry.execute(ResearchToolRequest(tool="markets", user_id="owner", as_of=NOW), scopes={"races:read"})
    unavailable = registry.execute(ResearchToolRequest(tool="races", user_id="owner", as_of=NOW), scopes={"races:read"})
    assert not_entitled.status == "NOT_ENTITLED"
    assert unavailable.status == "NOT_AVAILABLE"
    assert not_entitled.rows == unavailable.rows == []


def test_every_request_requires_timezone_aware_as_of_and_bounded_limit() -> None:
    with pytest.raises(ValidationError, match="as_of"):
        ResearchToolRequest(tool="races", user_id="owner", as_of=datetime(2026, 1, 15))
    with pytest.raises(ValidationError):
        ResearchToolRequest(tool="races", user_id="owner", as_of=NOW, limit=101)
