from pathlib import Path

import pytest

from app.external_provider_integrations import ProviderActivationError, TransportResponse
from app.live_provider_runtime import build_live_provider_handle, configured_provider_status, load_live_provider_config


def _env(**overrides: str) -> dict[str, str]:
    values = {
        "NEXUS_PROVIDER_PUNTERS_EDGE_ENABLED": "true",
        "NEXUS_PROVIDER_PUNTERS_EDGE_API_KEY": "local-test-key",
        "NEXUS_PROVIDER_PUNTERS_EDGE_APPROVAL_TIER": "HISTORICAL_RETENTION_AND_MODEL_TRAINING",
        "NEXUS_PROVIDER_PUNTERS_EDGE_APPROVED_OPERATIONS": "GET_RESULTS",
        "NEXUS_PROVIDER_PUNTERS_EDGE_APPROVED_CODES": "THOROUGHBRED",
        "NEXUS_PROVIDER_PUNTERS_EDGE_WRITTEN_RIGHTS": "rights",
        "NEXUS_PROVIDER_PUNTERS_EDGE_CREDENTIAL_POLICY": "credentials",
        "NEXUS_PROVIDER_PUNTERS_EDGE_RETENTION_TERMS": "retention",
        "NEXUS_PROVIDER_PUNTERS_EDGE_MODEL_TRAINING_PERMISSION": "training",
        "NEXUS_PROVIDER_PUNTERS_EDGE_DISPLAY_PERMISSION": "display",
        "NEXUS_PROVIDER_PUNTERS_EDGE_RECONCILIATION_REPORT": "reconciliation",
        "NEXUS_PROVIDER_PUNTERS_EDGE_ACCOUNT_ENTITLEMENT_EVIDENCE": "entitlement",
        "NEXUS_PROVIDER_PUNTERS_EDGE_CREDENTIAL_CUSTODIAN": "owner",
        "NEXUS_PROVIDER_PUNTERS_EDGE_QUOTA_CEILING": "one request",
        "NEXUS_PROVIDER_PUNTERS_EDGE_KILL_SWITCH_REFERENCE": "local kill switch",
    }
    values.update(overrides)
    return values


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def request(self, **kwargs: object) -> TransportResponse:
        self.calls.append(kwargs)
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        return TransportResponse(200, {"results": [{"race": "R1"}]}, now, now, "request-1")


def test_runtime_status_is_non_secret_and_does_not_make_network_request() -> None:
    statuses = configured_provider_status(environ=_env())
    punters = next(item for item in statuses if item["provider"] == "punters-edge")
    assert punters["enabled"] is True
    assert punters["credentials_configured"] is True
    assert punters["approval_status"] == "APPROVED"
    assert "local-test-key" not in str(statuses)


def test_private_read_approval_is_reported_as_approved_without_historical_rights() -> None:
    statuses = configured_provider_status(environ=_env(
        NEXUS_PROVIDER_PUNTERS_EDGE_APPROVAL_TIER="PRIVATE_SINGLE_OWNER_READ_ONLY",
        NEXUS_PROVIDER_PUNTERS_EDGE_WRITTEN_RIGHTS="",
        NEXUS_PROVIDER_PUNTERS_EDGE_CREDENTIAL_POLICY="",
        NEXUS_PROVIDER_PUNTERS_EDGE_RETENTION_TERMS="",
        NEXUS_PROVIDER_PUNTERS_EDGE_MODEL_TRAINING_PERMISSION="",
        NEXUS_PROVIDER_PUNTERS_EDGE_DISPLAY_PERMISSION="",
        NEXUS_PROVIDER_PUNTERS_EDGE_RECONCILIATION_REPORT="",
    ))
    punters = next(item for item in statuses if item["provider"] == "punters-edge")
    assert punters["approval_status"] == "APPROVED"


def test_runtime_requires_explicit_enable_flag() -> None:
    with pytest.raises(ProviderActivationError, match="disabled"):
        build_live_provider_handle("punters-edge", environ={"NEXUS_PROVIDER_PUNTERS_EDGE_API_KEY": "secret"}, transport=FakeTransport())


def test_runtime_injects_credentials_only_into_adapter_and_fetches_with_mock_transport() -> None:
    transport = FakeTransport()
    handle = build_live_provider_handle("punters-edge", environ=_env(), transport=transport)
    page = handle.adapter.fetch("GET_RESULTS", code="THOROUGHBRED", date="2026-10-12", approval=handle.config.approval)
    assert len(page.records) == 1
    assert transport.calls[0]["headers"] == {"X-API-Key": "local-test-key"}
    assert "local-test-key" not in page.records[0].model_dump_json()


def test_approval_file_cannot_contain_secret_fields(tmp_path: Path) -> None:
    approval_path = tmp_path / "approval.json"
    approval_path.write_text('{"api_key":"must-not-be-here"}', encoding="utf-8")
    values = _env(NEXUS_PROVIDER_PUNTERS_EDGE_APPROVAL_FILE=str(approval_path))
    with pytest.raises(ProviderActivationError, match="must not contain credentials"):
        load_live_provider_config("punters-edge", environ=values)


def test_diagnostic_approval_files_are_loaded_as_distinct_records(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    metadata.write_text(
        '{"approval_tier":"ACCOUNT_METADATA_READ","approved_operations":["ACCOUNT_METADATA_READ"],'
        '"approved_codes":["THOROUGHBRED"],"account_entitlement_evidence":"account",'
        '"credential_custodian":"owner","quota_ceiling":"one","kill_switch_reference":"local"}',
        encoding="utf-8",
    )
    diagnostic = tmp_path / "diagnostic.json"
    diagnostic.write_text(
        '{"approval_tier":"EPHEMERAL_READ_ONLY_DIAGNOSTIC","approved_operations":["GET_RESULTS"],'
        '"approved_codes":["THOROUGHBRED"],"account_entitlement_evidence":"account",'
        '"credential_custodian":"owner","quota_ceiling":"one","kill_switch_reference":"local"}',
        encoding="utf-8",
    )
    values = _env(
        NEXUS_DIAGNOSTICS_ENABLED="true",
        NEXUS_PROVIDER_PUNTERS_EDGE_ACCOUNT_METADATA_APPROVAL_FILE=str(metadata),
        NEXUS_PROVIDER_PUNTERS_EDGE_DIAGNOSTIC_APPROVAL_FILE=str(diagnostic),
    )
    config = load_live_provider_config("punters-edge", environ=values)
    assert set(config.diagnostic_approvals) == {"ACCOUNT_METADATA_READ", "EPHEMERAL_READ_ONLY_DIAGNOSTIC"}
