import pytest
from fastapi.testclient import TestClient

from app.auth import validate_bind_configuration
from app.main import app


@pytest.fixture
def authenticated_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ALLOW_LOCAL_AUTH", "true")
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("LOCAL_AUTH_TOKEN", "test-local-token")
    monkeypatch.setenv("LOCAL_AUTH_SCOPES", "races:read,forecasts:read,selections:read,selections:write")
    with TestClient(app) as client:
        yield client


def test_health_and_status_are_anonymous_and_correlated() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live", headers={"X-Correlation-ID": "corr-test-1"})
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.headers["X-Correlation-ID"] == "corr-test-1"

        status = client.get("/v1/system/status")
        assert status.status_code == 200
        assert status.json()["data_mode"] == "SYNTHETIC_ONLY"
        assert {item["provider"] for item in status.json()["providers"]} == {
            "formfav",
            "punters-edge",
            "krok-odds",
            "betfair-exchange",
        }
        assert status.headers["X-Correlation-ID"]


def test_cors_allows_only_the_configured_local_frontend() -> None:
    with TestClient(app) as client:
        allowed = client.get("/health/live", headers={"Origin": "http://127.0.0.1:5173"})
        assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"

        denied = client.get("/health/live", headers={"Origin": "https://untrusted.example"})
        assert "access-control-allow-origin" not in denied.headers


def test_domain_routes_fail_closed_with_stable_error_envelope() -> None:
    with TestClient(app) as client:
        response = client.get("/v1/codes")
        assert response.status_code == 401
        body = response.json()
        assert body["error"]["code"] == "UNAUTHORIZED"
        assert body["error"]["correlation_id"] == response.headers["X-Correlation-ID"]


def test_codes_route_has_bounded_paging_and_synthetic_labels(authenticated_client: TestClient) -> None:
    headers = {"Authorization": "Bearer test-local-token"}
    response = authenticated_client.get("/v1/codes?limit=100", headers=headers)
    assert response.status_code == 200
    assert response.json()["meta"]["limit"] == 100
    assert [item["code"] for item in response.json()["items"]] == ["THOROUGHBRED", "HARNESS", "GREYHOUND"]
    assert all(item["data_mode"] == "SYNTHETIC_ONLY" for item in response.json()["items"])

    invalid_limit = authenticated_client.get("/v1/codes?limit=101", headers=headers)
    assert invalid_limit.status_code == 400
    assert invalid_limit.json()["error"]["code"] == "BAD_REQUEST"

    invalid_cursor = authenticated_client.get("/v1/codes?cursor=forged", headers=headers)
    assert invalid_cursor.status_code == 400
    assert invalid_cursor.json()["error"]["code"] == "BAD_REQUEST"


def test_missing_race_and_selection_journal_are_stable(authenticated_client: TestClient) -> None:
    headers = {"Authorization": "Bearer test-local-token"}
    missing = authenticated_client.get("/v1/races/not-present", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"

    created = authenticated_client.post(
        "/v1/selections",
        json={"race_id": "race-1", "field_revision": "field-r1", "selection_type": "PASS", "rationale": "No evidence yet"},
        headers=headers,
    )
    assert created.status_code == 201
    selection_id = created.json()["selection_id"]
    listed = authenticated_client.get("/v1/selections", headers=headers)
    assert listed.status_code == 200
    assert any(item["selection_id"] == selection_id for item in listed.json()["items"])
    addendum = authenticated_client.post(
        f"/v1/selections/{selection_id}/addenda",
        json={"note": "Recorded as an immutable correction addendum."},
        headers=headers,
    )
    assert addendum.status_code == 201


def test_synthetic_catalog_routes_return_data_with_cursor_and_as_of(authenticated_client: TestClient) -> None:
    headers = {"Authorization": "Bearer test-local-token"}
    as_of = "2026-01-15T02:00:00Z"

    meetings = authenticated_client.get(f"/v1/meetings?limit=2&as_of={as_of}", headers=headers)
    assert meetings.status_code == 200
    assert len(meetings.json()["items"]) == 2
    assert meetings.json()["meta"]["next_cursor"]

    next_page = authenticated_client.get(
        f"/v1/meetings?limit=2&as_of={as_of}&cursor={meetings.json()['meta']['next_cursor']}",
        headers=headers,
    )
    assert next_page.status_code == 200
    assert len(next_page.json()["items"]) == 1

    race = authenticated_client.get(f"/v1/races/race:1?as_of={as_of}", headers=headers)
    assert race.status_code == 200
    entries = authenticated_client.get(f"/v1/races/race:1/entries?limit=2&as_of={as_of}", headers=headers)
    assert entries.status_code == 200
    assert len(entries.json()["items"]) == 2
    forecasts = authenticated_client.get(f"/v1/races/race:1/forecasts?as_of={as_of}", headers=headers)
    assert forecasts.status_code == 200
    assert len(forecasts.json()["items"]) == 1
    assert forecasts.json()["items"][0]["data_mode"] == "SYNTHETIC_ONLY"

    before_start = authenticated_client.get(
        "/v1/races/race:1?as_of=2026-01-15T00:59:59Z", headers=headers
    )
    assert before_start.status_code == 404


def test_invalid_token_and_missing_scope_fail_closed(authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    invalid = authenticated_client.get("/v1/codes", headers={"Authorization": "Bearer wrong"})
    assert invalid.status_code == 401

    monkeypatch.setenv("LOCAL_AUTH_SCOPES", "races:read")
    forbidden = authenticated_client.get(
        "/v1/races/race-1/forecasts", headers={"Authorization": "Bearer test-local-token"}
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"


def test_external_and_production_bind_modes_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ALLOW_LOCAL_AUTH", "true")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    with pytest.raises(RuntimeError, match="External API binds"):
        validate_bind_configuration()

    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(RuntimeError, match="Non-development"):
        validate_bind_configuration()
