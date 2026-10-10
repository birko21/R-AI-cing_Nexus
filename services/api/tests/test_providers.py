from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.provenance import RawEnvelope, payload_sha256
from app.providers import (
    AdapterContractError,
    AdapterPage,
    ContractedProviderAdapter,
    PaginationCapability,
    ProviderCapabilities,
    QuotaCapability,
    capability_matrix,
)


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def capabilities(**overrides: object) -> ProviderCapabilities:
    values: dict[str, object] = {
        "provider_id": "synthetic-fixture",
        "display_name": "Synthetic fixture adapter",
        "supported_codes": frozenset({"THOROUGHBRED", "HARNESS", "GREYHOUND"}),
        "supported_fields": frozenset({"meeting", "race", "entry", "result"}),
        "timestamp_fields": frozenset({"retrieved_at", "first_observed_at", "published_at"}),
        "data_mode": "SYNTHETIC_ONLY",
        "rights_state": "SYNTHETIC",
        "pagination": PaginationCapability(True, "CURSOR", 100),
        "quotas": QuotaCapability(requests_per_minute=60, daily_requests=1000, concurrent_requests=2),
        "supported_operations": frozenset({"LIST_MEETINGS", "GET_RACES", "GET_ENTRIES", "GET_RESULTS"}),
        "unsupported_operations": frozenset({"GET_MARKETS"}),
    }
    values.update(overrides)
    return ProviderCapabilities(**values)


def envelope(**overrides: object) -> RawEnvelope:
    payload = {"race": "THOROUGHBRED:synthetic-fixture:race-1", "value": 1}
    values: dict[str, object] = {
        "envelope_id": "env-1",
        "source_identifier": "synthetic://fixture/race-1",
        "payload": payload,
        "payload_sha256": payload_sha256(payload),
        "schema_version": "1.0",
        "retrieved_at": NOW,
        "first_observed_at": NOW,
        "data_mode": "SYNTHETIC_ONLY",
        "rights_state": "SYNTHETIC",
    }
    values.update(overrides)
    return RawEnvelope(**values)


class FixtureAdapter:
    def __init__(self, page: AdapterPage) -> None:
        self._capabilities = capabilities()
        self.page = page
        self.calls: list[tuple[str, str, str | None, int | None]] = []

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    def fetch(self, operation: str, *, code: str, cursor: str | None = None, page_size: int | None = None) -> AdapterPage:
        self.calls.append((operation, code, cursor, page_size))
        return self.page


def test_capability_matrix_reports_contract_fields() -> None:
    adapter = ContractedProviderAdapter(FixtureAdapter(AdapterPage((envelope(),), "next-1", NOW)))
    matrix = capability_matrix({"synthetic-fixture": adapter})

    assert matrix[0]["supported_codes"] == ["GREYHOUND", "HARNESS", "THOROUGHBRED"]
    assert matrix[0]["supported_operations"] == ["GET_ENTRIES", "GET_RACES", "GET_RESULTS", "LIST_MEETINGS"]
    assert matrix[0]["unsupported_operations"] == ["GET_MARKETS"]
    assert matrix[0]["quotas"]["requests_per_minute"] == 60
    assert matrix[0]["pagination"]["style"] == "CURSOR"


def test_adapter_returns_only_common_raw_envelopes_and_forwards_query() -> None:
    implementation = FixtureAdapter(AdapterPage((envelope(),), "next-1", NOW))
    adapter = ContractedProviderAdapter(implementation)

    page = adapter.fetch("GET_RACES", code="THOROUGHBRED", cursor="prior", page_size=10)

    assert isinstance(page.records[0], RawEnvelope)
    assert implementation.calls == [("GET_RACES", "THOROUGHBRED", "prior", 10)]


def test_unsupported_code_operation_and_page_size_are_rejected() -> None:
    implementation = FixtureAdapter(AdapterPage((envelope(),)))
    adapter = ContractedProviderAdapter(implementation)

    with pytest.raises(AdapterContractError, match="racing code"):
        adapter.fetch("GET_RACES", code="UNKNOWN")
    with pytest.raises(AdapterContractError, match="operation"):
        adapter.fetch("GET_MARKETS", code="THOROUGHBRED")
    with pytest.raises(AdapterContractError, match="page_size"):
        adapter.fetch("GET_RACES", code="THOROUGHBRED", page_size=101)


def test_page_cannot_claim_cursor_or_exceed_declared_limit() -> None:
    no_cursor = capabilities(pagination=PaginationCapability(False))
    implementation = FixtureAdapter(AdapterPage((envelope(),), "cursor"))
    implementation._capabilities = no_cursor
    with pytest.raises(AdapterContractError, match="pagination"):
        ContractedProviderAdapter(implementation).fetch("GET_RACES", code="THOROUGHBRED")

    too_many = FixtureAdapter(AdapterPage(tuple(envelope(envelope_id=f"env-{i}") for i in range(2))))
    too_many._capabilities = capabilities(pagination=PaginationCapability(True, "CURSOR", 1))
    with pytest.raises(AdapterContractError, match="page-size"):
        ContractedProviderAdapter(too_many).fetch("GET_RACES", code="THOROUGHBRED")


def test_record_mode_and_rights_must_match_declared_provider() -> None:
    implementation = FixtureAdapter(AdapterPage((envelope(data_mode="SCRAPED_PUBLIC", rights_state="UNASSESSED"),)))
    with pytest.raises(AdapterContractError, match="data mode"):
        ContractedProviderAdapter(implementation).fetch("GET_RACES", code="THOROUGHBRED")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"supported_codes": frozenset({"UNKNOWN"})},
        {"timestamp_fields": frozenset({"published_at"})},
        {"supported_operations": frozenset({"GET_RACES"}), "unsupported_operations": frozenset({"GET_RACES"})},
    ],
)
def test_capability_matrix_rejects_incomplete_or_conflicting_declarations(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        capabilities(**kwargs)
