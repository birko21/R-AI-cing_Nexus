from datetime import datetime
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.auth import forecasts_read, races_read, selections_read, selections_write, validate_bind_configuration
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
    Selection,
    SelectionAddendum,
    SelectionAddendumCreate,
    SelectionListResponse,
    SelectionCreate,
    SystemStatusResponse,
)
from app.pagination import paging_parameters
from app.selection_journal import SelectionJournal, SelectionJournalError


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

journal = SelectionJournal()


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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = {400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 501: "NOT_IMPLEMENTED"}.get(
        exc.status_code, "HTTP_ERROR"
    )
    return _error_response(request, code, str(exc.detail), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error_response(request, "BAD_REQUEST", "request validation failed", 400, {"errors": exc.errors()})


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
def live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/v1/system/status", response_model=SystemStatusResponse, tags=["system"])
def system_status() -> SystemStatusResponse:
    return SystemStatusResponse(
        app="racing-intelligence-lab",
        environment="development",
        data_mode="SYNTHETIC_ONLY",
        external_connectivity=False,
        model_status="NOT_TRAINED",
        wagering_enabled=False,
    )


def _page_meta(limit: int, as_of: datetime) -> PageMeta:
    return PageMeta(limit=limit, next_cursor=None, as_of=as_of)


@app.get("/v1/codes", response_model=CodeListResponse, tags=["races"], dependencies=[Depends(races_read)])
def list_codes(paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> CodeListResponse:
    limit, _, as_of = paging
    items = [
        CodeSummary(code="THOROUGHBRED", label="Thoroughbred", data_mode="SYNTHETIC_ONLY"),
        CodeSummary(code="HARNESS", label="Harness", data_mode="SYNTHETIC_ONLY"),
        CodeSummary(code="GREYHOUND", label="Greyhound", data_mode="SYNTHETIC_ONLY"),
    ]
    return CodeListResponse(items=items[:limit], meta=_page_meta(limit, as_of))


@app.get("/v1/meetings", response_model=MeetingListResponse, tags=["races"], dependencies=[Depends(races_read)])
def list_meetings(paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> MeetingListResponse:
    limit, _, as_of = paging
    return MeetingListResponse(items=[], meta=_page_meta(limit, as_of))


@app.get("/v1/races/{race_id}", response_model=Race, tags=["races"], dependencies=[Depends(races_read)])
def get_race(race_id: str, _: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> Race:
    raise HTTPException(status_code=404, detail=f"race {race_id} was not found")


@app.get("/v1/races/{race_id}/entries", response_model=EntryListResponse, tags=["races"], dependencies=[Depends(races_read)])
def list_entries(race_id: str, paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> EntryListResponse:
    limit, _, as_of = paging
    return EntryListResponse(items=[], meta=_page_meta(limit, as_of))


@app.get("/v1/races/{race_id}/forecasts", response_model=ForecastListResponse, tags=["forecasts"], dependencies=[Depends(forecasts_read)])
def list_forecasts(race_id: str, paging: tuple[int, str | None, datetime] = Depends(paging_parameters)) -> ForecastListResponse:
    limit, _, as_of = paging
    return ForecastListResponse(items=[], meta=_page_meta(limit, as_of))


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
