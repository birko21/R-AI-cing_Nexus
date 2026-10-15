from datetime import datetime
from datetime import date as calendar_date
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]


class ProviderRuntimeStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    enabled: bool
    credentials_configured: bool
    diagnostics_enabled: bool
    approval_status: str
    approval_missing_requirements: list[str]
    diagnostic_approval_tiers: list[str]


class ProviderProbeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["GET_RESULTS", "GET_ENTRIES"] = "GET_RESULTS"
    code: Literal["THOROUGHBRED"] = "THOROUGHBRED"
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    venue: str | None = Field(default=None, max_length=120)
    race: int | None = Field(default=None, ge=1, le=99)

    @field_validator("date")
    @classmethod
    def validate_calendar_date(cls, value: str) -> str:
        calendar_date.fromisoformat(value)
        return value


class ProviderDiagnosticCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_id: Literal["punters-edge"]
    operation: str
    code: Literal["THOROUGHBRED"]
    request_ordinal: int
    request_ceiling: int
    status_class: str
    row_count: int
    field_presence: list[str]
    quota_checked: bool
    raw_payload_retained: Literal[False]
    approval_reference: str


class ProviderProbeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["LIVE_DIAGNOSTIC_SUCCESS"]
    provider: Literal["punters-edge"]
    operation: Literal["GET_RESULTS", "GET_ENTRIES"]
    code: Literal["THOROUGHBRED"]
    checks: list[ProviderDiagnosticCheck]
    requests_used: int
    raw_payload_retained: Literal[False]


class LiveIngestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    venue: str | None = Field(default=None, max_length=120)
    race: int | None = Field(default=None, ge=1, le=99)

    @field_validator("date")
    @classmethod
    def validate_calendar_date(cls, value: str | None) -> str | None:
        if value is not None:
            calendar_date.fromisoformat(value)
        return value


class LiveIngestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["LIVE_INGESTION_SUCCESS"]
    provider: str
    operation: str
    code: Literal["THOROUGHBRED"]
    date: str
    persistence: dict[str, object]
    projection: dict[str, int]


class SystemStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: Literal["racing-intelligence-lab"]
    environment: str
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]
    external_connectivity: bool
    model_status: Literal["NOT_TRAINED", "ILLUSTRATIVE_ONLY", "MODEL_VALIDATED"]
    wagering_enabled: Literal[False]
    providers: list[ProviderRuntimeStatus]
    persistence: Literal["synthetic", "postgres"] = "synthetic"
    live_provider: str | None = None


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    correlation_id: str
    details: dict[str, object] | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


class PageMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(ge=1, le=100)
    next_cursor: str | None
    as_of: datetime


class CodeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Literal["THOROUGHBRED", "HARNESS", "GREYHOUND"]
    label: str
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]


class Meeting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meeting_id: str
    code: Literal["THOROUGHBRED", "HARNESS", "GREYHOUND"]
    name: str
    country: Literal["AUS"]
    scheduled_date: datetime
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]


class Race(BaseModel):
    model_config = ConfigDict(extra="forbid")

    race_id: str
    meeting_id: str
    race_number: int = Field(ge=1)
    status: Literal["SCHEDULED", "ACCEPTANCES", "FINAL_FIELDS", "OFFICIAL", "ABANDONED", "POSTPONED"]
    field_revision: str
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]
    source_receipt_id: str | None = None
    as_of: datetime | None = None


class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entry_id: str
    race_id: str
    participant_id: str
    number: int = Field(ge=1)
    name: str | None = None
    status: Literal["ACTIVE", "SCRATCHED", "RESERVE", "COUPLED"]
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]


class Forecast(BaseModel):
    model_config = ConfigDict(extra="forbid")

    forecast_id: str
    race_id: str
    field_revision: str
    cutoff: datetime
    model_version: str
    probabilities: dict[str, float]
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]
    diagnostic_flags: list[str] | None = None


class SelectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    race_id: str
    field_revision: str = Field(min_length=1)
    entry_id: str | None = None
    selection_type: Literal["WIN", "PLACE", "PASS"]
    rationale: str = Field(max_length=4000)
    forecast_id: str | None = None
    quote_id: str | None = None


class Selection(SelectionCreate):
    selection_id: str
    user_id: str
    created_at: datetime
    decision_time: datetime
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]


class SelectionAddendumCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str = Field(min_length=1, max_length=4000)


class SelectionAddendum(SelectionAddendumCreate):
    addendum_id: str
    selection_id: str
    user_id: str
    created_at: datetime


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    items: list[T]
    meta: PageMeta


class CodeListResponse(Page[CodeSummary]):
    pass


class MeetingListResponse(Page[Meeting]):
    pass


class EntryListResponse(Page[Entry]):
    pass


class ForecastListResponse(Page[Forecast]):
    pass


class SelectionListResponse(Page[Selection]):
    pass
