from datetime import datetime, timezone

import httpx
import pytest

from app.external_provider_integrations import (
    ProviderActivationError,
    HttpxReadOnlyTransport,
    TransportResponse,
    build_bounded_probe_plan,
    build_disabled_provider_adapters,
    build_existing_provider_assets,
)
from app.provider_diagnostics import BoundedDiagnosticSession, DiagnosticPolicy
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
        approval_tier="HISTORICAL_RETENTION_AND_MODEL_TRAINING",
        account_entitlement_evidence="owner-record:entitlement",
        credential_custodian="owner",
        quota_ceiling="6 requests per run",
        kill_switch_reference="diagnostics-disabled-by-default",
    )


def diagnostic_approval(provider: str, *operations: str) -> SourceApprovalRecord:
    return SourceApprovalRecord(
        provider,
        approved_operations=operations,
        approved_codes=("THOROUGHBRED",),
        approval_tier="EPHEMERAL_READ_ONLY_DIAGNOSTIC",
        account_entitlement_evidence="owner-record:account-entitlement",
        credential_custodian="owner",
        quota_ceiling="6 requests per run",
        kill_switch_reference="diagnostics-disabled-by-default",
    )


def metadata_approval(provider: str) -> SourceApprovalRecord:
    return SourceApprovalRecord(
        provider,
        approved_operations=("ACCOUNT_METADATA_READ",),
        approved_codes=("THOROUGHBRED",),
        approval_tier="ACCOUNT_METADATA_READ",
        account_entitlement_evidence="owner-record:account-entitlement",
        credential_custodian="owner",
        quota_ceiling="6 requests per run",
        kill_switch_reference="diagnostics-disabled-by-default",
    )


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def request(self, **kwargs: object) -> TransportResponse:
        self.calls.append(kwargs)
        payload: dict[str, object] = {"rows": [{"runner": "example"}]}
        if len(self.calls) == 1:
            payload = {"plan": "free", "credits_remaining": 2990, **payload}
        return TransportResponse(200, payload, NOW, NOW, "request-1")


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
    assert assets["punters-edge"].endpoint("ACCOUNT_METADATA_READ").path == "/v1/keys/info"
    assert assets["krok-odds"].endpoint("GET_ENTRIES").path == "/api/v1/racing/runner-form"
    assert assets["betfair-exchange"].endpoint("GET_MARKETS", view="book").description.startswith("listMarketBook")
    assert all(endpoint.read_only for asset in assets.values() for endpoint in asset.endpoints)
    assert all(asset.capabilities.supported_codes == {"THOROUGHBRED"} for asset in assets.values())


def test_bounded_probe_plan_is_a_plan_not_a_network_operation() -> None:
    plan = build_bounded_probe_plan("punters-edge", code="THOROUGHBRED", date="2026-09-19", venue="Randwick")

    assert plan.max_requests == 6
    assert plan.operations[0] == "ACCOUNT_METADATA_READ"
    assert plan.persistence == "DO_NOT_PERSIST_UNTIL_RETENTION_AND_MODEL_USE_ARE_APPROVED"


def test_full_named_approval_and_injected_transport_are_required() -> None:
    transport = FakeTransport()
    adapter = build_disabled_provider_adapters()["punters-edge"]
    active = adapter.__class__(adapter.asset, transport=transport, credential_resolver=lambda: "test-only-secret")

    with pytest.raises(ProviderActivationError, match="historical/model approval"):
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
    assert transport.calls[0]["headers"]["X-API-Key"] == "test-only-secret"
    assert transport.calls[0]["params"] == {"category": "horse", "date": "2026-09-19", "venue": "Randwick"}


def test_krok_uses_race_type_and_expands_racing_market_lines() -> None:
    transport = FakeTransport()
    adapter = build_disabled_provider_adapters()["krok-odds"]
    active = adapter.__class__(adapter.asset, transport=transport, credential_resolver=lambda: "test-only-secret")

    active.fetch(
        "LIST_MEETINGS", code="THOROUGHBRED", date="2026-10-17", venue="Randwick",
        approval=approval("krok-odds", "LIST_MEETINGS"),
    )
    active.fetch(
        "GET_MARKETS", code="THOROUGHBRED", date="2026-10-17", venue="Caulfield",
        approval=approval("krok-odds", "GET_MARKETS"),
    )
    active.fetch(
        "GET_RESULTS", code="THOROUGHBRED", date="2026-10-16",
        approval=approval("krok-odds", "GET_RESULTS"),
    )

    assert transport.calls[0]["params"]["race_type"] == "T"
    assert "code" not in transport.calls[0]["params"]
    assert transport.calls[0]["params"]["full"] == "1"
    assert transport.calls[0]["params"]["country"] == "AU"
    assert "include" not in transport.calls[1]["params"]
    assert transport.calls[2]["url"].endswith("/api/v1/racing/results/2026-10-16")


def test_formfav_uses_documented_australian_gallops_parameters() -> None:
    transport = FakeTransport()
    adapter = build_disabled_provider_adapters()["formfav"]
    active = adapter.__class__(adapter.asset, transport=transport, credential_resolver=lambda: "test-only-secret")
    active.fetch("GET_RACES", code="THOROUGHBRED", date="2026-10-17", venue="Randwick", approval=approval("formfav", "GET_RACES"))
    assert transport.calls[0]["params"]["race_code"] == "gallops"
    assert transport.calls[0]["params"]["country"] == "au"
    assert "code" not in transport.calls[0]["params"]


def test_http_transport_normalizes_top_level_results_array() -> None:
    class Response:
        status_code = 200
        headers = {"x-request-id": "request-1"}

        @staticmethod
        def json() -> list[dict[str, object]]:
            return [{"race_id": "race-1"}]

    class Client:
        @staticmethod
        def request(*args: object, **kwargs: object) -> Response:
            return Response()

    transport = HttpxReadOnlyTransport(client=Client())  # type: ignore[arg-type]
    response = transport.request(
        method="GET", url="https://provider.test/results", headers={}, params={},
        json_body=None, timeout_seconds=1.0,
    )

    assert response.payload == {"results": [{"race_id": "race-1"}]}


def test_betfair_adapter_uses_read_only_json_rpc_and_never_post_settlement_sp_as_pre_race_input() -> None:
    transport = FakeTransport()
    asset = build_existing_provider_assets()["betfair-exchange"]
    adapter = build_disabled_provider_adapters()["betfair-exchange"].__class__(
        asset, transport=transport, credential_resolver=lambda: {"app_key": "test-only-app", "session_token": "test-only-session"},
    )

    adapter.fetch(
        "GET_MARKETS", code="THOROUGHBRED", view="book",
        market_ids=("1.234567890",),
        approval=approval("betfair-exchange", "GET_MARKETS"),
    )

    body = transport.calls[0]["json_body"]
    assert body["method"].endswith("listMarketBook")
    assert transport.calls[0]["method"] == "POST"
    assert "starting_price" not in body["params"]


def test_diagnostic_session_requires_metadata_first_and_retains_only_aggregate_output() -> None:
    transport = FakeTransport()
    base = build_disabled_provider_adapters()["punters-edge"]
    adapter = base.__class__(base.asset, transport=transport, credential_resolver=lambda: "test-only-secret")
    session = BoundedDiagnosticSession(
        adapter,
        approval={
            "ACCOUNT_METADATA_READ": metadata_approval("punters-edge"),
            "EPHEMERAL_READ_ONLY_DIAGNOSTIC": diagnostic_approval("punters-edge", "GET_RESULTS", "GET_ENTRIES"),
        },
        code="THOROUGHBRED",
        policy=DiagnosticPolicy(enabled=True),
    )

    metadata = session.run("ACCOUNT_METADATA_READ")
    results = session.run("GET_RESULTS", date="2026-09-19", venue="Randwick")

    assert transport.calls[0]["url"].endswith("/v1/keys/info")
    assert transport.calls[0]["headers"] == {"X-API-Key": "test-only-secret"}
    assert transport.calls[0]["params"] == {}
    assert metadata.quota_checked is True
    assert results.raw_payload_retained is False
    assert results.row_count > 0
    assert "runner" in results.field_presence
    assert session.requests_used == 2
    assert "test-only-secret" not in str(metadata)
    assert "test-only-secret" not in str(results)


def test_account_metadata_rejects_invalid_quota_values() -> None:
    class InvalidQuotaTransport(FakeTransport):
        def request(self, **kwargs: object) -> TransportResponse:
            self.calls.append(kwargs)
            return TransportResponse(200, {"plan": "free", "credits_remaining": -1}, NOW, NOW, "request-1")

    transport = InvalidQuotaTransport()
    base = build_disabled_provider_adapters()["punters-edge"]
    adapter = base.__class__(base.asset, transport=transport, credential_resolver=lambda: "test-only-secret")
    session = BoundedDiagnosticSession(
        adapter,
        approval=metadata_approval("punters-edge"),
        code="THOROUGHBRED",
        policy=DiagnosticPolicy(enabled=True, max_requests=1),
    )

    with pytest.raises(ProviderActivationError, match="invalid quota"):
        session.run("ACCOUNT_METADATA_READ")


def test_account_metadata_cannot_be_fetched_as_a_raw_envelope() -> None:
    base = build_disabled_provider_adapters()["punters-edge"]
    adapter = base.__class__(base.asset, transport=FakeTransport(), credential_resolver=lambda: "test-only-secret")

    with pytest.raises(ProviderActivationError, match="aggregate-only"):
        adapter.fetch("ACCOUNT_METADATA_READ", code="THOROUGHBRED", approval=metadata_approval("punters-edge"))


def test_diagnostic_session_has_no_pagination_or_retry_path() -> None:
    transport = FakeTransport()
    base = build_disabled_provider_adapters()["punters-edge"]
    adapter = base.__class__(base.asset, transport=transport, credential_resolver=lambda: "test-only-secret")
    session = BoundedDiagnosticSession(
        adapter,
        approval=metadata_approval("punters-edge"),
        code="THOROUGHBRED",
        policy=DiagnosticPolicy(enabled=True),
    )

    with pytest.raises(ValueError, match="pagination"):
        session.run("ACCOUNT_METADATA_READ", cursor="next")
    with pytest.raises(ValueError, match="first diagnostic"):
        BoundedDiagnosticSession(
            adapter,
            approval=diagnostic_approval("punters-edge", "GET_RESULTS"),
            code="THOROUGHBRED",
            policy=DiagnosticPolicy(enabled=True),
        ).run("GET_RESULTS")


def test_http_transport_converts_upstream_http_failure_to_safe_activation_error() -> None:
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429, json={"error": "quota"})))
    transport = HttpxReadOnlyTransport(client=client)
    try:
        with pytest.raises(ProviderActivationError, match="HTTP 429"):
            transport.request(method="GET", url="https://provider.invalid", headers={}, params={}, json_body=None, timeout_seconds=1)
    finally:
        transport.close()


def test_http_transport_rejects_non_json_provider_payload() -> None:
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"not-json")))
    transport = HttpxReadOnlyTransport(client=client)
    try:
        with pytest.raises(ProviderActivationError, match="valid JSON"):
            transport.request(method="GET", url="https://provider.invalid", headers={}, params={}, json_body=None, timeout_seconds=1)
    finally:
        transport.close()
