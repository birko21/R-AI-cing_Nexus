from datetime import datetime, timezone

import pytest

from app.external_provider_integrations import (
    ProviderActivationError,
    TransportResponse,
    build_bounded_probe_plan,
    build_disabled_provider_adapters,
    build_existing_provider_assets,
)
from app.source_approval import SourceApprovalRecord


NOW = datetime(2026, 10, 10, 8, tzinfo=timezone.utc)


def approval(provider: str, *operations: str) -> SourceApprovalRecord:
    return SourceApprovalRecord(
        provider,
        written_rights="owner-record:rights",
        credential_policy="owner-record:credentials-server-side",
        retention_terms="owner-record:retention",
        model_training_permission="owner-record:training",
        display_permission="owner-record:derived-display",
        reconciliation_report="owner-record:identity-reconciliation",
        approved_operations=operations,
        approved_codes=("THOROUGHBRED",),
    )


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def request(self, **kwargs: object) -> TransportResponse:
        self.calls.append(kwargs)
        return TransportResponse(200, {"rows": [{"runner": "example"}]}, NOW, NOW, "request-1")


def test_default_registry_is_disabled_and_has_no_transport_or_credentials() -> None:
    adapters = build_disabled_provider_adapters()

    assert set(adapters) == {"formfav", "punters-edge", "krok-odds", "betfair-exchange"}
    assert all(not adapter.capabilities.enabled for adapter in adapters.values())
    with pytest.raises(ProviderActivationError, match="disabled"):
        adapters["formfav"].fetch("LIST_MEETINGS", code="THOROUGHBRED")


def test_audited_endpoint_inventory_is_read_only_and_scoped_to_thoroughbred() -> None:
    assets = build_existing_provider_assets()

    assert assets["formfav"].endpoint("GET_RACES").path == "/v1/form"
    assert assets["punters-edge"].endpoint("GET_RESULTS").path == "/v1/racing/results"
    assert assets["krok-odds"].endpoint("GET_ENTRIES").path == "/api/v1/racing/runner-form"
    assert assets["betfair-exchange"].endpoint("GET_MARKETS", view="book").description.startswith("listMarketBook")
    assert all(endpoint.read_only for asset in assets.values() for endpoint in asset.endpoints)
    assert all(asset.capabilities.supported_codes == {"THOROUGHBRED"} for asset in assets.values())


def test_bounded_probe_plan_is_a_plan_not_a_network_operation() -> None:
    plan = build_bounded_probe_plan("punters-edge", code="THOROUGHBRED", date="2026-09-19", venue="Randwick")

    assert plan.max_requests == 2
    assert plan.persistence == "DO_NOT_PERSIST_UNTIL_RETENTION_AND_MODEL_USE_ARE_APPROVED"


def test_full_named_approval_and_injected_transport_are_required() -> None:
    transport = FakeTransport()
    adapter = build_disabled_provider_adapters()["punters-edge"]
    active = adapter.__class__(adapter.asset, transport=transport, credential_resolver=lambda: "test-only-secret")

    with pytest.raises(ProviderActivationError, match="does not name"):
        active.fetch("GET_RESULTS", code="THOROUGHBRED", approval=approval("punters-edge", "GET_ENTRIES"))
    with pytest.raises(ProviderActivationError, match="does not match"):
        active.fetch("GET_RESULTS", code="THOROUGHBRED", approval=approval("formfav", "GET_RESULTS"))

    page = active.fetch(
        "GET_RESULTS", code="THOROUGHBRED", date="2026-09-19", venue="Randwick",
        approval=approval("punters-edge", "GET_RESULTS"),
    )

    assert len(page.records) == 1
    assert page.records[0].rights_state == "APPROVED"
    assert transport.calls[0]["method"] == "GET"
    assert transport.calls[0]["url"].endswith("/v1/racing/results")
    assert "test-only-secret" in transport.calls[0]["headers"]["Authorization"]


def test_betfair_adapter_uses_read_only_json_rpc_and_never_post_settlement_sp_as_pre_race_input() -> None:
    transport = FakeTransport()
    asset = build_existing_provider_assets()["betfair-exchange"]
    adapter = build_disabled_provider_adapters()["betfair-exchange"].__class__(
        asset, transport=transport, credential_resolver=lambda: {"app_key": "test-only-app", "session_token": "test-only-session"},
    )

    adapter.fetch(
        "GET_MARKETS", code="THOROUGHBRED", view="book",
        approval=approval("betfair-exchange", "GET_MARKETS"),
    )

    body = transport.calls[0]["json_body"]
    assert body["method"].endswith("listMarketBook")
    assert transport.calls[0]["method"] == "POST"
    assert "starting_price" not in body["params"]
