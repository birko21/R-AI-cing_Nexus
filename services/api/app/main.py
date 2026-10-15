from datetime import datetime
from contextlib import asynccontextmanager
import hmac
import os
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.auth import forecasts_read, providers_read, races_read, selections_read, selections_write, validate_bind_configuration
from app.catalog_repository import PostgresCatalogRepository, SyntheticCatalogRepository, offset_from_cursor
from app.database_config import sqlalchemy_database_url
from app.contracts import (
    CodeSummary,
    CodeListResponse,
    EntryListResponse,
    ErrorResponse,
    ForecastListResponse,
    HealthResponse,
    MeetingListResponse,
    PageMeta,
    Race,
    RaceListResponse,
    Selection,
    SelectionAddendum,
    SelectionAddendumCreate,
    SelectionListResponse,
    SelectionCreate,
    SystemStatusResponse,
    ProviderDiagnosticCheck,
    ProviderProbeRequest,
    ProviderProbeResponse,
    LiveIngestionRequest,
    LiveIngestionResponse,
)
from app.external_provider_integrations import ProviderActivationError
from app.live_ingestion_runner import run_live_ingestion
from app.live_provider_runtime import build_live_provider_handle, configured_provider_status
from app.pagination import paging_parameters
from app.provider_diagnostics import BoundedDiagnosticSession, DiagnosticPolicy
from app.selection_journal import PostgresSelectionJournal, SelectionJournal, SelectionJournalError
from app.runtime_config import load_runtime_config


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_bind_configuration()
    yield

app = FastAPI(
    title="Racing Intelligence Lab API",
    version="0.1.0",
    description="Local-only offline MVP API foundation.",
    lifespan=lifespan,
)

def _runtime_repositories():
    runtime = load_runtime_config()
    if runtime.persistence == "postgres":
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is required when NEXUS_API_PERSISTENCE=postgres")
        from sqlalchemy import create_engine

        engine = create_engine(sqlalchemy_database_url(database_url), pool_pre_ping=True)
        return PostgresSelectionJournal(engine), PostgresCatalogRepository(engine)
    if runtime.data_mode != "SYNTHETIC_ONLY":
        raise RuntimeError("non-synthetic data modes require PostgreSQL persistence")
    return SelectionJournal(), SyntheticCatalogRepository()


journal, catalog = _runtime_repositories()


def _cors_origins() -> list[str]:
    configured = [item.strip().rstrip("/") for item in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if item.strip()]
    if configured:
        if "*" in configured or any("*" in origin for origin in configured):
            raise RuntimeError("CORS_ALLOWED_ORIGINS must be an explicit origin allowlist")
        return configured
    if os.environ.get("APP_ENV", "development") == "development":
        return ["http://127.0.0.1:5173", "http://localhost:5173"]
    raise RuntimeError("CORS_ALLOWED_ORIGINS is required outside development")


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", str(uuid4()))


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


def _error_response(request: Request, code: str, message: str, status_code: int, details: dict[str, object] | None = None):
    body = ErrorResponse(
        error={"code": code, "message": message, "correlation_id": _correlation_id(request), "details": details}
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"), headers={"X-Correlation-ID": _correlation_id(request)})


def _json_safe_validation_errors(errors: list[dict[str, object]]) -> list[dict[str, object]]:
    def sanitize(value: object) -> object:
        if isinstance(value, BaseException):
            return str(value)
        if isinstance(value, dict):
            return {str(key): sanitize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [sanitize(item) for item in value]
        return value

    return sanitize(errors)  # type: ignore[return-value]


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = {400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 501: "NOT_IMPLEMENTED"}.get(
        exc.status_code, "HTTP_ERROR"
    )
    return _error_response(request, code, str(exc.detail), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error_response(request, "BAD_REQUEST", "request validation failed", 400, {"errors": _json_safe_validation_errors(exc.errors())})


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
def live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/v1/system/status", response_model=SystemStatusResponse, tags=["system"])
def system_status() -> SystemStatusResponse:
    runtime = load_runtime_config()
    providers = list(configured_provider_status())
    return SystemStatusResponse(
        app="racing-intelligence-lab",
        environment=os.environ.get("APP_ENV", "development"),
        data_mode=runtime.data_mode,
        external_connectivity=any(
            bool(item.get("enabled")) and bool(item.get("credentials_configured"))
            for item in providers
        ),
        model_status="NOT_TRAINED",
        wagering_enabled=False,
        providers=providers,
        persistence=runtime.persistence,
        live_provider=runtime.live_provider,
    )


@app.post("/v1/provider-probes/punters-edge", response_model=ProviderProbeResponse, tags=["providers"], dependencies=[Depends(providers_read)])
def probe_punters_edge(payload: ProviderProbeRequest) -> ProviderProbeResponse:
    """Run one bounded, aggregate-only PuntersEdge connectivity check."""

    handle = None
    try:
        handle = build_live_provider_handle("punters-edge")
        if not handle.config.diagnostics_enabled:
            raise ProviderActivationError("provider diagnostics are disabled by the kill switch")
        session = BoundedDiagnosticSession(
            handle.adapter,
            approval=handle.config.diagnostic_approvals,
            code=payload.code,
            policy=DiagnosticPolicy(enabled=True),
        )
        checks = [session.run("ACCOUNT_METADATA_READ")]
        checks.append(session.run(payload.operation, date=payload.date, venue=payload.venue, race=payload.race))
        return ProviderProbeResponse(
            status="LIVE_DIAGNOSTIC_SUCCESS",
            provider="punters-edge",
            operation=payload.operation,
            code=payload.code,
            checks=[ProviderDiagnosticCheck(**check.__dict__) for check in checks],
            requests_used=session.requests_used,
            raw_payload_retained=False,
        )
    except (ProviderActivationError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"provider probe blocked: {exc}") from exc
    finally:
        if handle is not None:
            handle.close()


def require_ingestion_trigger(authorization: str | None = Header(default=None)) -> None:
    configured = os.environ.get("NEXUS_INGESTION_TRIGGER_TOKEN", "").strip()
    if not configured:
        raise HTTPException(status_code=503, detail="live ingestion trigger is not configured")
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not supplied or not hmac.compare_digest(supplied, configured):
        raise HTTPException(status_code=401, detail="live ingestion trigger authentication failed")


@app.post(
    "/internal/live-ingestion/run",
    response_model=LiveIngestionResponse,
    include_in_schema=False,
    tags=["internal"],
    dependencies=[Depends(require_ingestion_trigger)],
)
def run_live_ingestion_endpoint(payload: LiveIngestionRequest | None = None) -> LiveIngestionResponse:
    try:
        result = run_live_ingestion(
            date=payload.date if payload else None,
            venue=payload.venue if payload else None,
            race=payload.race if payload else None,
        )
        return LiveIngestionResponse(**result)
    except (ProviderActivationError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"live ingestion blocked: {exc}") from exc


def _page_meta(limit: int, as_of: datetime, *, offset: int = 0, has_more: bool = False) -> PageMeta:
    from app.pagination import encode_cursor

    next_cursor = encode_cursor(as_of, offset + limit, {}) if has_more else None
    return PageMeta(limit=limit, next_cursor=next_cursor, as_of=as_of)


@app.get("/v1/codes", response_model=CodeListResponse, tags=["races"], dependencies=[Depends(races_read)])
def list_codes(paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> CodeListResponse:
    limit, _, as_of = paging
    data_mode = load_runtime_config().data_mode
    codes = ("THOROUGHBRED",) if data_mode != "SYNTHETIC_ONLY" else ("THOROUGHBRED", "HARNESS", "GREYHOUND")
    labels = {"THOROUGHBRED": "Thoroughbred", "HARNESS": "Harness", "GREYHOUND": "Greyhound"}
    items = [
        CodeSummary(code=code, label=labels[code], data_mode=data_mode)
        for code in codes
    ]
    return CodeListResponse(items=items[:limit], meta=_page_meta(limit, as_of))


@app.get("/v1/meetings", response_model=MeetingListResponse, tags=["races"], dependencies=[Depends(races_read)])
def list_meetings(paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> MeetingListResponse:
    limit, cursor, as_of = paging
    offset = offset_from_cursor(cursor, as_of=as_of)
    items, has_more = catalog.list_meetings(limit=limit, offset=offset, as_of=as_of)
    return MeetingListResponse(items=items, meta=_page_meta(limit, as_of, offset=offset, has_more=has_more))


@app.get("/v1/meetings/{meeting_id}/races", response_model=RaceListResponse, tags=["races"], dependencies=[Depends(races_read)])
def list_races_for_meeting(meeting_id: str, paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> RaceListResponse:
    limit, cursor, as_of = paging
    offset = offset_from_cursor(cursor, as_of=as_of)
    items, has_more = catalog.list_races(meeting_id, limit=limit, offset=offset, as_of=as_of)
    return RaceListResponse(items=items, meta=_page_meta(limit, as_of, offset=offset, has_more=has_more))


@app.get("/v1/races/{race_id}", response_model=Race, tags=["races"], dependencies=[Depends(races_read)])
def get_race(race_id: str, paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> Race:
    race = catalog.get_race(race_id, as_of=paging[2])
    if race is None:
        raise HTTPException(status_code=404, detail=f"race {race_id} was not found")
    return race


@app.get("/v1/races/{race_id}/entries", response_model=EntryListResponse, tags=["races"], dependencies=[Depends(races_read)])
def list_entries(race_id: str, paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> EntryListResponse:
    limit, cursor, as_of = paging
    if catalog.get_race(race_id, as_of=as_of) is None:
        raise HTTPException(status_code=404, detail=f"race {race_id} was not found")
    offset = offset_from_cursor(cursor, as_of=as_of)
    items, has_more = catalog.list_entries(race_id, limit=limit, offset=offset, as_of=as_of)
    return EntryListResponse(items=items, meta=_page_meta(limit, as_of, offset=offset, has_more=has_more))


@app.get("/v1/races/{race_id}/forecasts", response_model=ForecastListResponse, tags=["forecasts"], dependencies=[Depends(forecasts_read)])
def list_forecasts(race_id: str, paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> ForecastListResponse:
    limit, cursor, as_of = paging
    if catalog.get_race(race_id, as_of=as_of) is None:
        raise HTTPException(status_code=404, detail=f"race {race_id} was not found")
    offset = offset_from_cursor(cursor, as_of=as_of)
    items, has_more = catalog.list_forecasts(race_id, limit=limit, offset=offset, as_of=as_of)
    return ForecastListResponse(items=items, meta=_page_meta(limit, as_of, offset=offset, has_more=has_more))


@app.get("/v1/selections", response_model=SelectionListResponse, tags=["selections"])
def list_selections(auth: dict[str, object] = Depends(selections_read), paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> SelectionListResponse:
    limit, _, as_of = paging
    return SelectionListResponse(items=journal.list_for_user(str(auth["subject"]))[:limit], meta=_page_meta(limit, as_of))


@app.post("/v1/selections", response_model=Selection, status_code=201, tags=["selections"])
def create_selection(payload: SelectionCreate, auth: dict[str, object] = Depends(selections_write)) -> Selection:
    try:
        return journal.create(str(auth["subject"]), payload)
    except SelectionJournalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/selections/{selection_id}/addenda", response_model=SelectionAddendum, status_code=201, tags=["selections"])
def create_selection_addendum(selection_id: str, payload: SelectionAddendumCreate, auth: dict[str, object] = Depends(selections_write)) -> SelectionAddendum:
    try:
        return journal.addendum(str(auth["subject"]), selection_id, payload)
    except SelectionJournalError as exc:
        status = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
