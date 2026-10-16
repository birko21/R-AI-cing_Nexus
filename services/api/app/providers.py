"""Provider capability and adapter contract for approved data sources."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal, Protocol

from app.domain import VALID_CODES
from app.provenance import DataMode, RawEnvelope, RightsState


ProviderOperation = Literal[
    "LIST_MEETINGS",
    "GET_RACES",
    "GET_ENTRIES",
    "GET_ACCEPTANCES",
    "GET_RESULTS",
    "GET_MARKETS",
    "ACCOUNT_METADATA_READ",
]
TimestampField = Literal["retrieved_at", "first_observed_at", "published_at"]
PaginationStyle = Literal["NONE", "CURSOR", "PAGE_NUMBER"]

KNOWN_OPERATIONS = frozenset({"LIST_MEETINGS", "GET_RACES", "GET_ENTRIES", "GET_ACCEPTANCES", "GET_RESULTS", "GET_MARKETS", "ACCOUNT_METADATA_READ"})
KNOWN_TIMESTAMP_FIELDS = frozenset({"retrieved_at", "first_observed_at", "published_at"})


@dataclass(frozen=True)
class PaginationCapability:
    supported: bool
    style: PaginationStyle = "NONE"
    max_page_size: int | None = None

    def __post_init__(self) -> None:
        if not self.supported and self.style != "NONE":
            raise ValueError("unsupported pagination must use NONE style")
        if self.supported and self.style == "NONE":
            raise ValueError("supported pagination must declare a style")
        if self.max_page_size is not None and self.max_page_size < 1:
            raise ValueError("max_page_size must be positive")


@dataclass(frozen=True)
class QuotaCapability:
    requests_per_minute: int | None = None
    daily_requests: int | None = None
    concurrent_requests: int | None = None
    unknown: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        values = (self.requests_per_minute, self.daily_requests, self.concurrent_requests)
        if any(value is not None and value < 1 for value in values):
            raise ValueError("reported quotas must be positive")
        if not self.unknown and all(value is None for value in values):
            raise ValueError("quota limits must be reported or explicitly marked unknown")


@dataclass(frozen=True)
class ProviderCapabilities:
    provider_id: str
    display_name: str
    supported_codes: frozenset[str]
    supported_fields: frozenset[str]
    timestamp_fields: frozenset[str]
    data_mode: DataMode
    rights_state: RightsState
    pagination: PaginationCapability
    quotas: QuotaCapability
    supported_operations: frozenset[str]
    unsupported_operations: frozenset[str]
    enabled: bool = True

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.provider_id.strip() or not self.display_name.strip():
            raise ValueError("provider identity is required")
        if not self.supported_codes or not self.supported_codes.issubset(VALID_CODES):
            raise ValueError("supported_codes must contain only known racing codes")
        if not self.supported_fields:
            raise ValueError("at least one supported field is required")
        if not self.timestamp_fields.issubset(KNOWN_TIMESTAMP_FIELDS):
            raise ValueError("timestamp_fields contains an unknown timestamp")
        if not {"retrieved_at", "first_observed_at"}.issubset(self.timestamp_fields):
            raise ValueError("raw-envelope timestamps must be supported")
        if not self.supported_operations.issubset(KNOWN_OPERATIONS):
            raise ValueError("supported_operations contains an unknown operation")
        if not self.unsupported_operations.issubset(KNOWN_OPERATIONS):
            raise ValueError("unsupported_operations contains an unknown operation")
        if self.supported_operations & self.unsupported_operations:
            raise ValueError("an operation cannot be both supported and unsupported")

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "supported_codes": sorted(self.supported_codes),
            "supported_fields": sorted(self.supported_fields),
            "timestamp_fields": sorted(self.timestamp_fields),
            "data_mode": self.data_mode,
            "rights_state": self.rights_state,
            "pagination": asdict(self.pagination),
            "quotas": asdict(self.quotas),
            "supported_operations": sorted(self.supported_operations),
            "unsupported_operations": sorted(self.unsupported_operations),
            "enabled": self.enabled,
        }


@dataclass(frozen=True)
class AdapterPage:
    records: tuple[RawEnvelope, ...]
    next_cursor: str | None = None
    as_of: datetime | None = None

    def __post_init__(self) -> None:
        if any(not isinstance(record, RawEnvelope) for record in self.records):
            raise TypeError("adapter records must use the common RawEnvelope")
        if self.as_of is not None and (self.as_of.tzinfo is None or self.as_of.utcoffset() is None):
            raise ValueError("adapter page as_of must be timezone-aware")


class ProviderAdapter(Protocol):
    @property
    def capabilities(self) -> ProviderCapabilities: ...

    def fetch(
        self,
        operation: ProviderOperation,
        *,
        code: str,
        cursor: str | None = None,
        page_size: int | None = None,
    ) -> AdapterPage: ...


class AdapterContractError(ValueError):
    """Raised when a provider violates its declared capability contract."""


def validate_adapter_page(capabilities: ProviderCapabilities, page: AdapterPage) -> None:
    if not capabilities.enabled:
        raise AdapterContractError("provider is disabled")
    if page.next_cursor is not None and not capabilities.pagination.supported:
        raise AdapterContractError("provider returned a cursor without pagination support")
    limit = capabilities.pagination.max_page_size
    if limit is not None and len(page.records) > limit:
        raise AdapterContractError("provider returned more records than its page-size capability")
    for record in page.records:
        if record.data_mode != capabilities.data_mode:
            raise AdapterContractError("record data mode does not match provider capability")
        if record.rights_state != capabilities.rights_state:
            raise AdapterContractError("record rights state does not match provider capability")


class ContractedProviderAdapter:
    """Runtime guard around an adapter implementation."""

    def __init__(self, adapter: ProviderAdapter) -> None:
        self._adapter = adapter
        self.capabilities = adapter.capabilities
        self.capabilities.validate()

    def capability_matrix(self) -> dict[str, object]:
        return self.capabilities.to_dict()

    def fetch(
        self,
        operation: ProviderOperation,
        *,
        code: str,
        cursor: str | None = None,
        page_size: int | None = None,
    ) -> AdapterPage:
        if code not in self.capabilities.supported_codes:
            raise AdapterContractError(f"provider does not support racing code {code}")
        if operation in self.capabilities.unsupported_operations or operation not in self.capabilities.supported_operations:
            raise AdapterContractError(f"provider does not support operation {operation}")
        if page_size is not None and page_size < 1:
            raise AdapterContractError("page_size must be positive")
        if page_size is not None and self.capabilities.pagination.max_page_size is not None and page_size > self.capabilities.pagination.max_page_size:
            raise AdapterContractError("requested page_size exceeds provider capability")
        page = self._adapter.fetch(operation, code=code, cursor=cursor, page_size=page_size)
        validate_adapter_page(self.capabilities, page)
        return page


def capability_matrix(adapters: Mapping[str, ContractedProviderAdapter]) -> list[dict[str, object]]:
    """Return deterministic, reviewable capability evidence for registered adapters."""
    return [adapters[key].capability_matrix() for key in sorted(adapters)]
