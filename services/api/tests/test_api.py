import pytest
from fastapi.testclient import TestClient

from app.auth import require_bearer
from app.main import app


@pytest.fixture
def authenticated_client():
    app.dependency_overrides[require_bearer] = lambda: None
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_health_and_status_are_anonymous_and_correlated() -> None:
    response = TestClient(app).get("/health/live", headers={"X-Correlation-ID": "corr-test-1"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Correlation-ID"] == "corr-test-1"

    status = TestClient(app).get("/v1/system/status")
    assert status.status_code == 200
    assert status.json()["data_mode"] == "SYNTHETIC_ONLY"
    assert status.headers["X-Correlation-ID"]


def test_domain_routes_fail_closed_with_stable_error_envelope() -> None:
    response = TestClient(app).get("/v1/codes")
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["correlation_id"] == response.headers["X-Correlation-ID"]


def test_codes_route_has_bounded_paging_and_synthetic_labels(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/v1/codes?limit=100")
    assert response.status_code == 200
    assert response.json()["meta"]["limit"] == 100
    assert [item["code"] for item in response.json()["items"]] == ["THOROUGHBRED", "HARNESS", "GREYHOUND"]
    assert all(item["data_mode"] == "SYNTHETIC_ONLY" for item in response.json()["items"])

    invalid_limit = authenticated_client.get("/v1/codes?limit=101")
    assert invalid_limit.status_code == 400
    assert invalid_limit.json()["error"]["code"] == "BAD_REQUEST"

    invalid_cursor = authenticated_client.get("/v1/codes?cursor=forged")
    assert invalid_cursor.status_code == 400
    assert invalid_cursor.json()["error"]["code"] == "BAD_REQUEST"


def test_missing_race_and_unimplemented_selection_are_stable_errors(authenticated_client: TestClient) -> None:
    missing = authenticated_client.get("/v1/races/not-present")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"

    pending = authenticated_client.post(
        "/v1/selections",
        json={"race_id": "race-1", "selection_type": "PASS", "rationale": "No evidence yet"},
    )
    assert pending.status_code == 501
    assert pending.json()["error"]["code"] == "NOT_IMPLEMENTED"
