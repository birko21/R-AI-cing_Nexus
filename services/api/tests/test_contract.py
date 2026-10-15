from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app.contracts import HealthResponse, SystemStatusResponse
from app.main import app


ROOT = Path(__file__).parents[3]
CONTRACT_PATH = ROOT / "contracts" / "openapi_mvp.yaml"


def test_openapi_contract_has_versioned_mvp_surfaces() -> None:
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract["openapi"] == "3.1.0"
    assert contract["info"]["version"] == "1.0.0"
    assert {
        "/health/live",
        "/v1/system/status",
        "/v1/codes",
        "/v1/meetings",
        "/v1/meetings/{meeting_id}/races",
        "/v1/races/{race_id}",
        "/v1/races/{race_id}/entries",
        "/v1/races/{race_id}/forecasts",
        "/v1/selections",
    }.issubset(contract["paths"])

    schemas = contract["components"]["schemas"]
    for schema_name in (
        "HealthResponse",
        "SystemStatusResponse",
        "ErrorResponse",
        "CodeSummary",
        "Meeting",
        "Race",
        "Entry",
        "Forecast",
        "Selection",
    ):
        assert schema_name in schemas

    assert schemas["PageMeta"]["properties"]["limit"]["maximum"] == 100
    assert schemas["SystemStatusResponse"]["properties"]["external_connectivity"]["type"] == "boolean"
    assert schemas["SystemStatusResponse"]["properties"]["wagering_enabled"]["const"] is False
    scopes = contract["components"]["securitySchemes"]["bearerAuth"]["flows"]["clientCredentials"]["scopes"]
    assert set(scopes) == {"races:read", "forecasts:read", "selections:read", "selections:write", "providers:read"}


def test_foundation_runtime_matches_shared_response_models() -> None:
    client = TestClient(app)

    live_response = client.get("/health/live")
    status_response = client.get("/v1/system/status")

    assert live_response.status_code == 200
    assert status_response.status_code == 200
    assert HealthResponse.model_validate(live_response.json()).status == "ok"
    status = SystemStatusResponse.model_validate(status_response.json())
    assert status.data_mode == "SYNTHETIC_ONLY"
    assert status.external_connectivity is False
    assert status.wagering_enabled is False

    generated = app.openapi()["components"]["schemas"]
    assert set(generated["HealthResponse"]["required"]) == {"status"}
    assert set(generated["SystemStatusResponse"]["required"]) == {
        "app",
        "environment",
        "data_mode",
        "external_connectivity",
        "model_status",
        "wagering_enabled",
        "providers",
    }
