"""Fail-closed, read-only adapters for the existing provider assets.

This module deliberately contains endpoint contracts, not credentials.  The
default factory returns disabled adapters.  A caller must supply an explicit
operation/code approval record and an injected server-side transport before a
request can be made.  This keeps auditability and testing possible without
turning application startup into an external network operation.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Literal, Protocol
from uuid import uuid4

import httpx

from app.domain import VALID_CODES
from app.provenance import RawEnvelope, payload_sha256
from app.providers import (
    AdapterContractError,
    AdapterPage,
    ProviderCapabilities,
    ProviderOperation,
    QuotaCapability,
    PaginationCapability,
    validate_adapter_page,
)
from app.source_approval import ApprovalTier, SourceApprovalRecord, evaluate_tiered_source_approval


ProviderId = Literal["formfav", "punters-edge", "krok-odds", "betfair-exchange"]
MarketView = Literal["catalogue", "book"]
CredentialMaterial = str | Mapping[str, str]
CredentialResolver = Callable[[], CredentialMaterial | None]


class ProviderActivationError(RuntimeError):
    """Raised when a provider request is not explicitly eligible to run."""


def _safe_provider_error_code(payload: Mapping[str, object]) -> str | None:
    """Extract a bounded provider error code without retaining response text."""

    candidates: list[object] = [payload]
    nested = payload.get("error")
    if isinstance(nested, Mapping):
        candidates.append(nested)
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        for key in ("errorCode", "error_code", "code"):
            value = candidate.get(key)
            if isinstance(value, (str, int)) and str(value).strip():
                return str(value).strip()[:80]
    return None


@dataclass(frozen=True)
class EndpointSpec:
    operation: str
    method: str
    path: str
    description: str
    read_only: bool = True


@dataclass(frozen=True)
class TransportResponse:
    status_code: int
    payload: Mapping[str, object]
    retrieved_at: datetime
    published_at: datetime | None = None
    request_id: str = ""


class ReadOnlyTransport(Protocol):
    def request(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        params: Mapping[str, object],
        json_body: Mapping[str, object] | None,
        timeout_seconds: float,
        form_body: Mapping[str, str] | None = None,
    ) -> TransportResponse: ...


class HttpxReadOnlyTransport:
    """Small HTTP transport; it is only reachable through an active adapter."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(follow_redirects=False)

    def close(self) -> None:
        self._client.close()

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        params: Mapping[str, object],
        json_body: Mapping[str, object] | None,
        timeout_seconds: float,
        form_body: Mapping[str, str] | None = None,
    ) -> TransportResponse:
        try:
            response = self._client.request(
                method,
                url,
                headers=dict(headers),
                params=dict(params),
                json=json_body,
                data=dict(form_body) if form_body is not None else None,
                timeout=timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise ProviderActivationError("provider request failed") from exc
        if response.status_code < 200 or response.status_code >= 300:
            raise ProviderActivationError(f"provider returned HTTP {response.status_code}")
        try:
            body = response.json()
        except ValueError as exc:
            raise ProviderActivationError("provider response was not valid JSON") from exc
        if isinstance(body, list):
            # PuntersEdge returns the results collection as a top-level JSON
            # array. Normalize that transport shape before it crosses the
            # common envelope boundary; projection still validates every row.
            body = {"results": body}
        if not isinstance(body, dict):
            raise ProviderActivationError("provider response must be a JSON object or array")
        retrieved_at = datetime.now(timezone.utc)
        return TransportResponse(
            status_code=response.status_code,
            payload=body,
            retrieved_at=retrieved_at,
            request_id=response.headers.get("x-request-id", ""),
        )


@dataclass(frozen=True)
class ExistingProviderAsset:
    provider_id: ProviderId
    display_name: str
    base_url: str
    endpoints: tuple[EndpointSpec, ...]
    capabilities: ProviderCapabilities
    evidence_summary: tuple[str, ...]
    rights_summary: tuple[str, ...]

    def endpoint(self, operation: str, *, view: MarketView = "catalogue") -> EndpointSpec:
        candidates = tuple(item for item in self.endpoints if item.operation == operation)
        if self.provider_id == "betfair-exchange" and operation == "GET_MARKETS":
            wanted = "listMarketBook" if view == "book" else "listMarketCatalogue"
            candidates = tuple(item for item in candidates if item.description.startswith(wanted))
        if not candidates:
            raise AdapterContractError(f"{self.provider_id} does not declare {operation}")
        endpoint = candidates[0]
        if not endpoint.read_only:
            raise ProviderActivationError("non-read-only endpoint rejected")
        return endpoint


def _capabilities(
    provider_id: ProviderId,
    display_name: str,
    fields: frozenset[str],
    operations: frozenset[str],
    quota: QuotaCapability,
) -> ProviderCapabilities:
    return ProviderCapabilities(
        provider_id=provider_id,
        display_name=display_name,
        supported_codes=frozenset({"THOROUGHBRED"}),
        supported_fields=fields,
        timestamp_fields=frozenset({"retrieved_at", "first_observed_at", "published_at"}),
        data_mode="LICENSED",
        rights_state="UNASSESSED",
        pagination=PaginationCapability(False),
        quotas=quota,
        supported_operations=operations,
        unsupported_operations=frozenset(VALID_OPERATIONS - operations),
        enabled=False,
    )


VALID_OPERATIONS = {"LIST_MEETINGS", "GET_RACES", "GET_ENTRIES", "GET_ACCEPTANCES", "GET_RESULTS", "GET_MARKETS", "ACCOUNT_METADATA_READ"}


class BetfairSessionTokenManager:
    """Runtime-login session manager modelled on The Long Straight's adapter.

    The manager deliberately depends on the injected read-only transport so
    tests cannot accidentally make an external request and production callers
    retain one bounded HTTP policy for login and JSON-RPC calls.
    """

    def __init__(self, *, transport: ReadOnlyTransport, app_key: str, username: str, password: str) -> None:
        if not app_key.strip() or not username.strip() or not password:
            raise ProviderActivationError("Betfair runtime login requires app key, username and password")
        self._transport = transport
        self._app_key = app_key
        self._username = username
        self._password = password
        self._token: str | None = None

    def token(self) -> str:
        if self._token:
            return self._token
        response = self._transport.request(
            method="POST",
            url="https://identitysso.betfair.com/api/login",
            headers={"X-Application": self._app_key, "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            params={},
            json_body=None,
            form_body={"username": self._username, "password": self._password},
            timeout_seconds=4.0,
        )
        if response.status_code < 200 or response.status_code >= 300:
            raise ProviderActivationError(f"Betfair login failed with HTTP {response.status_code}")
        token = response.payload.get("token")
        if not isinstance(token, str) or not token.strip():
            raise ProviderActivationError("Betfair login response did not contain a session token")
        self._token = token.strip()
        return self._token

    def invalidate(self) -> None:
        self._token = None


def build_existing_provider_assets() -> dict[str, ExistingProviderAsset]:
    """Return endpoint/capability evidence with external access disabled."""

    return {
        "formfav": ExistingProviderAsset(
            "formfav", "FormFav", "https://api.formfav.com",
            (
                EndpointSpec("LIST_MEETINGS", "GET", "/v1/form/meetings", "meeting catalogue"),
                EndpointSpec("GET_RACES", "GET", "/v1/form", "race card and runner form"),
            ),
            _capabilities("formfav", "FormFav", frozenset({"meeting", "race", "distance_m", "barrier", "jockey", "trainer", "weight", "form", "scratch_flag"}), frozenset({"LIST_MEETINGS", "GET_RACES"}), QuotaCapability(unknown=True, notes="Plan and quota not evidenced in the audited sibling records.")),
            ("Sibling adapter hard-codes AU gallops/thoroughbred and provides meeting/race-card fields.", "No committed sanitized live response was found in the audit snapshot."),
            ("Account access was confirmed by the owner; plan, retention and model-use terms for Nexus remain unrecorded."),
        ),
        "punters-edge": ExistingProviderAsset(
            "punters-edge", "PuntersEdge", "https://api.puntersedge.online",
            (
                EndpointSpec("GET_RESULTS", "GET", "/v1/racing/results", "historical results and settled fixed prices"),
                EndpointSpec("GET_ACCEPTANCES", "GET", "/v1/racing/acceptances", "full-day Australian pre-race acceptance card"),
                EndpointSpec("GET_ENTRIES", "GET", "/v1/racing/horses/form", "horse history/form"),
                EndpointSpec("ACCOUNT_METADATA_READ", "GET", "/v1/keys/info", "account metadata and quota"),
            ),
            _capabilities("punters-edge", "PuntersEdge", frozenset({"race_id", "runner_id", "start_time", "resulted_at", "position", "dead_heat", "fixed_win_price", "fixed_place_price", "horse_form", "acceptances", "barrier", "weight", "jockey", "trainer", "last10", "ratings", "gear", "scratchings"}), frozenset({"ACCOUNT_METADATA_READ", "GET_RESULTS", "GET_ENTRIES", "GET_ACCEPTANCES", "GET_RACES"}), QuotaCapability(unknown=True, notes="A sanitized sibling probe recorded remaining credits; exact current quota is not independently re-verified here.")),
            ("Sibling sanitized validation recorded 10 final AU thoroughbred races, 9 complete, with fixed Win/Place prices.", "Personal free-plan evidence is historical evidence, not a Nexus entitlement record."),
            ("Nexus retention, training and derived-display permission is not evidenced; no transfer from the sibling application is assumed."),
        ),
        "krok-odds": ExistingProviderAsset(
            "krok-odds", "Krok Odds", "https://krokodds.com.au",
            (
                EndpointSpec("LIST_MEETINGS", "GET", "/api/v1/racing/meetings", "racing meetings"),
                EndpointSpec("GET_MARKETS", "GET", "/api/v1/odds-feed/racing", "odds enrichment"),
                EndpointSpec("GET_ENTRIES", "GET", "/api/v1/racing/runner-form", "runner form"),
                EndpointSpec("GET_RESULTS", "GET", "/api/v1/racing/results/{date}", "date-scoped results"),
            ),
            _capabilities("krok-odds", "Krok Odds", frozenset({"meeting", "race", "runner_id", "distance_m", "barrier", "jockey", "trainer", "win_price", "place_price", "win_bsp", "source_classification", "recent_finishes", "result_position", "sectionals", "response_timestamp"}), frozenset({"LIST_MEETINGS", "GET_MARKETS", "GET_ENTRIES", "GET_RESULTS"}), QuotaCapability(requests_per_minute=5, daily_requests=50, unknown=False, notes="Sibling docs report free-tier limits; observed api tier and current commercial terms require account evidence.")),
            ("Sibling probes returned AU thoroughbred finishing rows and runner/form/odds shapes.", "The recheck did not establish complete numeric tote/BSP evidence or durable historical depth."),
            ("Non-transferable key and intended-use review are documented in the sibling; Nexus retention/training/display rights remain open."),
        ),
        "betfair-exchange": ExistingProviderAsset(
            "betfair-exchange", "Betfair Exchange", "https://api-au.betfair.com/exchange/betting/json-rpc/v1",
            (
                EndpointSpec("GET_MARKETS", "POST", "", "listMarketCatalogue read-only market identity"),
                EndpointSpec("GET_MARKETS", "POST", "", "listMarketBook read-only prices and volume"),
            ),
            _capabilities("betfair-exchange", "Betfair Exchange", frozenset({"market_id", "market_start_time", "selection_id", "runner_name", "runner_status", "pre_race_prices", "available_volume", "matched_volume", "starting_price"}), frozenset({"GET_MARKETS"}), QuotaCapability(unknown=True, notes="API/app-key limits and market-data charges are not evidenced in the audited records.")),
            ("Sibling evidence validates AU horse event type 7 catalogue/book shapes and delayed SP projections.", "Historical movement/liquidity retention is not established; catalogue capture and book reads remain separate phases."),
            ("Betfair market-data, retention, training and derived-display permissions for Nexus are unresolved."),
        ),
    }


def _formfav_track_slug(value: str) -> str:
    """Match FormFav's documented track-slug query field."""

    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if not slug:
        raise ProviderActivationError("FormFav venue cannot be converted to a track slug")
    return slug


@dataclass(frozen=True)
class BoundedProbePlan:
    provider_id: str
    code: str
    date: str
    venue: str | None
    max_requests: int
    operations: tuple[str, ...]
    persistence: str
    validation_checks: tuple[str, ...]


def build_bounded_probe_plan(provider_id: str, *, code: str, date: str, venue: str | None = None) -> BoundedProbePlan:
    assets = build_existing_provider_assets()
    if provider_id not in assets:
        raise ValueError(f"unknown provider asset: {provider_id}")
    if code not in VALID_CODES:
        raise ValueError(f"unsupported racing code: {code}")
    if code != "THOROUGHBRED":
        raise ValueError("audited provider assets do not establish this racing code")
    operations = {
        "formfav": ("LIST_MEETINGS", "GET_RACES"),
        "punters-edge": ("ACCOUNT_METADATA_READ", "GET_RESULTS", "GET_RESULTS", "GET_ENTRIES", "GET_ENTRIES", "GET_ENTRIES"),
        "krok-odds": ("LIST_MEETINGS", "GET_ENTRIES", "GET_MARKETS", "GET_RESULTS"),
        "betfair-exchange": ("GET_MARKETS",),
    }[provider_id]
    return BoundedProbePlan(
        provider_id, code, date, venue, len(operations), operations,
        "DO_NOT_PERSIST_UNTIL_RETENTION_AND_MODEL_USE_ARE_APPROVED",
        ("source identity and runner identity", "observation/publication timestamps", "pre-race eligibility", "duplicate and post-race fields", "quota and response-size limits"),
    )


class GatedReadOnlyProviderAdapter:
    """Provider-specific request builder with an explicit activation gate."""

    def __init__(self, asset: ExistingProviderAsset, *, transport: ReadOnlyTransport | None = None, credential_resolver: CredentialResolver | None = None) -> None:
        self.asset = asset
        self._transport = transport
        self._credential_resolver = credential_resolver
        self._betfair_session_manager: BetfairSessionTokenManager | None = None

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.asset.capabilities

    def _check_runtime(self) -> None:
        if self._transport is None or self._credential_resolver is None:
            raise ProviderActivationError("server-side transport and credential resolver are required")

    def _check_gate(self, operation: ProviderOperation, code: str, approval: SourceApprovalRecord | None) -> SourceApprovalRecord:
        if approval is None:
            raise ProviderActivationError("external provider access is disabled until a named approval record is supplied")
        required_tier = "PRIVATE_SINGLE_OWNER_READ_ONLY" if approval.approval_tier == "PRIVATE_SINGLE_OWNER_READ_ONLY" else "HISTORICAL_RETENTION_AND_MODEL_TRAINING"
        checkpoint = evaluate_tiered_source_approval(approval, required_tier=required_tier, operation=operation, code=code)
        if checkpoint.status != "APPROVED":
            label = "private live-read" if required_tier == "PRIVATE_SINGLE_OWNER_READ_ONLY" else "historical/model"
            raise ProviderActivationError(f"{label} approval is incomplete: {','.join(checkpoint.missing_requirements)}")
        if approval.source_id != self.asset.provider_id:
            raise ProviderActivationError("approval source does not match provider")
        self._check_runtime()
        return approval

    def _check_diagnostic_gate(self, operation: str, code: str, approval: SourceApprovalRecord | None) -> SourceApprovalRecord:
        if approval is None:
            raise ProviderActivationError("diagnostics are disabled until a named approval record is supplied")
        required_tier: ApprovalTier = "ACCOUNT_METADATA_READ" if operation == "ACCOUNT_METADATA_READ" else "EPHEMERAL_READ_ONLY_DIAGNOSTIC"
        checkpoint = evaluate_tiered_source_approval(
            approval, required_tier=required_tier, operation=operation, code=code,
        )
        if checkpoint.status != "APPROVED":
            raise ProviderActivationError(f"diagnostic approval is incomplete: {','.join(checkpoint.missing_requirements)}")
        if approval.source_id != self.asset.provider_id:
            raise ProviderActivationError("approval source does not match provider")
        self._check_runtime()
        return approval

    def _credentials(self) -> tuple[Mapping[str, str], dict[str, str]]:
        assert self._credential_resolver is not None
        credentials = self._credential_resolver()
        if not credentials:
            raise ProviderActivationError("credential resolver returned no credential")
        if isinstance(credentials, str):
            normalized: Mapping[str, str] = {"token": credentials, "api_key": credentials}
        else:
            normalized = credentials
        if self.asset.provider_id in {"punters-edge", "formfav", "krok-odds"}:
            api_key = normalized.get("api_key") or normalized.get("token")
            if not api_key:
                raise ProviderActivationError(f"{self.asset.display_name} requires a server-side API key")
            return normalized, {"X-API-Key": api_key}
        return normalized, {}

    def _betfair_session_token(self, credentials: Mapping[str, str]) -> tuple[str, bool]:
        """Return a session token and whether it came from runtime login."""

        static_token = credentials.get("session_token", "").strip()
        if static_token:
            return static_token, False
        app_key = credentials.get("app_key", "").strip()
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "")
        if not app_key or not username or not password:
            raise ProviderActivationError(
                "Betfair requires server-side app key and either session token or username/password"
            )
        if self._transport is None:
            raise ProviderActivationError("server-side transport is required for Betfair runtime login")
        if self._betfair_session_manager is None:
            self._betfair_session_manager = BetfairSessionTokenManager(
                transport=self._transport, app_key=app_key, username=username, password=password,
            )
        return self._betfair_session_manager.token(), True

    def _invalidate_betfair_session(self) -> None:
        if self._betfair_session_manager is not None:
            self._betfair_session_manager.invalidate()

    @staticmethod
    def _request_params(
        operation: str,
        *,
        provider_id: ProviderId | None = None,
        code: str,
        date: str | None,
        venue: str | None,
        race: int | None,
        cursor: str | None = None,
        page_size: int | None = None,
        market_ids: tuple[str, ...] | None = None,
    ) -> dict[str, object]:
        if operation == "ACCOUNT_METADATA_READ":
            if any(value is not None for value in (date, venue, race, cursor, page_size)):
                raise ProviderActivationError("PuntersEdge account metadata accepts no query parameters")
            return {}
        if operation == "GET_RESULTS" and code == "THOROUGHBRED" and provider_id == "punters-edge":
            # PuntersEdge names the thoroughbred category "horse" and does
            # not accept the application's generic `code` query parameter.
            params = {"category": "horse"}
            for key, value in (("date", date), ("venue", venue), ("limit", page_size)):
                if value is not None:
                    params[key] = value
            return params
        if provider_id == "punters-edge" and operation == "GET_ACCEPTANCES":
            params = {"date": date} if date is not None else {}
            if venue is not None:
                params["venue"] = venue
            return params
        if provider_id == "punters-edge" and operation == "GET_RACES":
            params = {"venue": venue, "meeting_date": date, "race_number": race} if venue is not None and date is not None and race is not None else {}
            return {key: value for key, value in params.items() if value is not None}
        # Krok uses its own racing-code vocabulary and silently ignores the
        # generic `code` parameter.  Use `race_type=T` for the board, odds and
        # dated-result endpoints so a broad all-code response cannot be
        # mistaken for a thoroughbred-only response.
        if provider_id == "krok-odds":
            params = {"race_type": "T" if code == "THOROUGHBRED" else code}
            if operation == "LIST_MEETINGS":
                params["full"] = "1"
                params["country"] = "AU"
        elif provider_id == "formfav":
            # FormFav's card API uses the sibling adapter's documented AU
            # gallops vocabulary rather than the Nexus racing-code token.
            if operation == "GET_RACES":
                params = {
                    "track": _formfav_track_slug(venue) if venue is not None else "",
                    "timezone": "Australia/Sydney",
                    "race_code": "gallops",
                    "country": "au",
                }
            else:
                params = {"race_code": "gallops", "country": "au", "timezone": "Australia/Sydney"}
        else:
            params = {"code": code}
        for key, value in (("date", date), ("venue", venue), ("race", race), ("cursor", cursor), ("limit", page_size)):
            if provider_id == "formfav" and operation == "GET_RACES" and key == "venue":
                continue
            if value is not None:
                params[key] = value
        return params

    @staticmethod
    def _betfair_params(
        *,
        view: MarketView,
        date: str | None,
        venue: str | None,
        market_ids: tuple[str, ...] | None,
        page_size: int | None,
    ) -> dict[str, object]:
        """Build bounded API-NG request parameters, never order operations."""

        if view == "book":
            if not market_ids:
                raise ProviderActivationError("Betfair listMarketBook requires explicit market IDs from a catalogue response")
            return {
                "marketIds": list(market_ids[:20]),
                "priceProjection": {"priceData": ["EX_BEST_OFFERS", "EX_TRADED", "SP_AVAILABLE", "SP_TRADED"]},
            }
        market_filter: dict[str, object] = {"eventTypeIds": ["7"], "marketTypeCodes": ["WIN"], "marketCountries": ["AU"]}
        if date:
            market_filter["marketStartTime"] = {
                "from": f"{date}T00:00:00Z",
                "to": f"{date}T23:59:59Z",
            }
        if venue:
            market_filter["venues"] = [venue]
        return {
            "filter": market_filter,
            "marketProjection": ["EVENT", "COMPETITION", "MARKET_START_TIME", "RUNNER_DESCRIPTION", "RUNNER_METADATA"],
            "maxResults": min(page_size or 100, 100),
        }

    def fetch(self, operation: ProviderOperation, *, code: str, approval: SourceApprovalRecord | None = None, date: str | None = None, venue: str | None = None, race: int | None = None, view: MarketView = "catalogue", cursor: str | None = None, page_size: int | None = None, market_ids: tuple[str, ...] | None = None) -> AdapterPage:
        if operation == "ACCOUNT_METADATA_READ":
            raise ProviderActivationError("account metadata must use the aggregate-only diagnostic path")
        approved = self._check_gate(operation, code, approval)
        if code not in self.capabilities.supported_codes:
            raise AdapterContractError(f"provider does not support racing code {code}")
        endpoint = self.asset.endpoint(operation, view=view)
        credentials, headers = self._credentials()
        params = self._request_params(
            operation, provider_id=self.asset.provider_id, code=code, date=date, venue=venue, race=race, cursor=cursor, page_size=page_size,
        )
        body: dict[str, object] | None = None
        runtime_login = False
        if self.asset.provider_id == "betfair-exchange":
            app_key = credentials.get("app_key", "") if isinstance(credentials, Mapping) else ""
            session_token, runtime_login = self._betfair_session_token(credentials)
            if not app_key:
                raise ProviderActivationError("Betfair requires a server-side app key")
            headers = {"X-Application": app_key, "X-Authentication": session_token, "Content-Type": "application/json"}
            method_name = endpoint.description.split(" ", 1)[0]
            params = self._betfair_params(view=view, date=date, venue=venue, market_ids=market_ids, page_size=page_size)
            body = {"jsonrpc": "2.0", "method": f"SportsAPING/v1.0/{method_name}", "params": params, "id": 1}
            params = {}
        path = endpoint.path.replace("{date}", date or "")
        assert self._transport is not None
        try:
            response = self._transport.request(method=endpoint.method, url=f"{self.asset.base_url}{path}", headers=headers, params=params, json_body=body, timeout_seconds=4.0)
        except ProviderActivationError as exc:
            if not (runtime_login and any(marker in str(exc) for marker in ("HTTP 401", "HTTP 403"))):
                raise
            self._invalidate_betfair_session()
            refreshed_token, _ = self._betfair_session_token(credentials)
            headers = {"X-Application": credentials.get("app_key", ""), "X-Authentication": refreshed_token, "Content-Type": "application/json"}
            response = self._transport.request(method=endpoint.method, url=f"{self.asset.base_url}{path}", headers=headers, params=params, json_body=body, timeout_seconds=4.0)
        if response.status_code < 200 or response.status_code >= 300:
            detail = f"provider returned HTTP {response.status_code}"
            error_code = _safe_provider_error_code(response.payload)
            if error_code:
                detail += f" ({error_code})"
            raise ProviderActivationError(detail)
        if self.asset.provider_id == "betfair-exchange" and isinstance(response.payload.get("error"), Mapping):
            error_code = _safe_provider_error_code(response.payload)
            if error_code and error_code != "INVALID_SESSION":
                raise ProviderActivationError(f"Betfair API error ({error_code})")
        if runtime_login and isinstance(response.payload.get("error"), Mapping):
            error_text = " ".join(str(value) for value in response.payload["error"].values()).upper()
            if "INVALID_SESSION" in error_text:
                self._invalidate_betfair_session()
                refreshed_token, _ = self._betfair_session_token(credentials)
                headers = {"X-Application": credentials.get("app_key", ""), "X-Authentication": refreshed_token, "Content-Type": "application/json"}
                response = self._transport.request(method=endpoint.method, url=f"{self.asset.base_url}{path}", headers=headers, params=params, json_body=body, timeout_seconds=4.0)
                if response.status_code < 200 or response.status_code >= 300:
                    raise ProviderActivationError(f"provider returned HTTP {response.status_code}")
        retrieved_at = response.retrieved_at
        payload = dict(response.payload)
        payload["_request"] = {"provider": self.asset.provider_id, "operation": operation, "code": code, "date": date, "venue": venue, "race": race, "view": view}
        envelope = RawEnvelope(
            envelope_id=str(uuid4()), source_identifier=f"{self.asset.provider_id}:{operation}", payload=payload,
            payload_sha256=payload_sha256(payload), schema_version="provider-response-v1", retrieved_at=retrieved_at,
            first_observed_at=response.published_at or retrieved_at, published_at=response.published_at,
            data_mode="LICENSED", rights_state="APPROVED", licence_reference=approved.source_id,
            retrieval_metadata={"http_status": response.status_code, "request_id": response.request_id, "credentials": "server-side"},
        )
        enabled = ProviderCapabilities(**{**self.capabilities.to_dict(), "supported_codes": frozenset(self.capabilities.supported_codes), "supported_fields": frozenset(self.capabilities.supported_fields), "timestamp_fields": frozenset(self.capabilities.timestamp_fields), "data_mode": "LICENSED", "rights_state": "APPROVED", "pagination": PaginationCapability(False), "quotas": self.capabilities.quotas, "supported_operations": frozenset(self.capabilities.supported_operations), "unsupported_operations": frozenset(self.capabilities.unsupported_operations), "enabled": True})
        page = AdapterPage((envelope,), as_of=retrieved_at)
        validate_adapter_page(enabled, page)
        return page

    def diagnostic(
        self,
        operation: str,
        *,
        code: str,
        approval: SourceApprovalRecord | None = None,
        date: str | None = None,
        venue: str | None = None,
        race: int | None = None,
        view: MarketView = "catalogue",
        market_ids: tuple[str, ...] | None = None,
        request_ordinal: int = 1,
        request_ceiling: int = 6,
    ) -> "SanitizedDiagnostic":
        """Perform one approved read and return aggregate metadata only."""

        approved = self._check_diagnostic_gate(operation, code, approval)
        if request_ordinal < 1 or request_ordinal > request_ceiling or request_ceiling > 6:
            raise ProviderActivationError("diagnostic request ceiling must be between 1 and 6")
        endpoint = self.asset.endpoint(operation, view=view)
        credentials, headers = self._credentials()
        params = self._request_params(operation, provider_id=self.asset.provider_id, code=code, date=date, venue=venue, race=race)
        body: dict[str, object] | None = None
        runtime_login = False
        if self.asset.provider_id == "betfair-exchange":
            app_key = credentials.get("app_key", "")
            session_token, runtime_login = self._betfair_session_token(credentials)
            if not app_key:
                raise ProviderActivationError("Betfair requires a server-side app key")
            headers = {"X-Application": app_key, "X-Authentication": session_token, "Content-Type": "application/json"}
            method_name = endpoint.description.split(" ", 1)[0]
            params = self._betfair_params(view=view, date=date, venue=venue, market_ids=market_ids, page_size=None)
            body = {"jsonrpc": "2.0", "method": f"SportsAPING/v1.0/{method_name}", "params": params, "id": 1}
            params = {}
        assert self._transport is not None
        path = endpoint.path.replace("{date}", date or "")
        response = self._transport.request(
            method=endpoint.method, url=f"{self.asset.base_url}{path}", headers=headers,
            params=params, json_body=body, timeout_seconds=4.0,
        )
        if response.status_code < 200 or response.status_code >= 300:
            raise ProviderActivationError(f"provider returned HTTP {response.status_code}")
        fields = _field_presence(response.payload)
        quota_checked = False
        if operation == "ACCOUNT_METADATA_READ":
            _validate_account_metadata(response.payload)
            quota_checked = True
        return SanitizedDiagnostic(
            provider_id=self.asset.provider_id, operation=operation, code=code,
            request_ordinal=request_ordinal, request_ceiling=request_ceiling,
            status_class=f"{response.status_code // 100}xx", row_count=_aggregate_row_count(response.payload),
            field_presence=fields, quota_checked=quota_checked,
            raw_payload_retained=False, approval_reference=approved.source_id,
        )


@dataclass(frozen=True)
class SanitizedDiagnostic:
    provider_id: str
    operation: str
    code: str
    request_ordinal: int
    request_ceiling: int
    status_class: str
    row_count: int
    field_presence: tuple[str, ...]
    quota_checked: bool
    raw_payload_retained: bool
    approval_reference: str


def _field_presence(value: object, *, _depth: int = 0) -> tuple[str, ...]:
    if _depth > 3:
        return ()
    if isinstance(value, list):
        fields: set[str] = set()
        for item in value[:100]:
            fields.update(_field_presence(item, _depth=_depth + 1))
        return tuple(sorted(fields))
    if not isinstance(value, Mapping):
        return ()
    fields: set[str] = set()
    for key, nested in value.items():
        if isinstance(key, str) and key not in {"token", "key", "password", "secret", "authorization"}:
            fields.add(key)
        fields.update(_field_presence(nested, _depth=_depth + 1))
    return tuple(sorted(fields))


def _field_values(value: object, names: set[str], *, _depth: int = 0) -> tuple[object, ...]:
    if _depth > 4:
        return ()
    if isinstance(value, list):
        values: list[object] = []
        for item in value[:100]:
            values.extend(_field_values(item, names, _depth=_depth + 1))
        return tuple(values)
    if not isinstance(value, Mapping):
        return ()
    values: list[object] = []
    for key, nested in value.items():
        if isinstance(key, str) and key.lower() in names:
            values.append(nested)
        values.extend(_field_values(nested, names, _depth=_depth + 1))
    return tuple(values)


def _nonnegative_number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return value >= 0
    if isinstance(value, str):
        try:
            return float(value.strip()) >= 0
        except ValueError:
            return False
    return False


def _validate_account_metadata(payload: Mapping[str, object]) -> None:
    plans = _field_values(payload, {"plan"})
    if not any(isinstance(value, str) and value.strip() for value in plans):
        raise ProviderActivationError("account metadata response did not expose a plan")
    quota_values = _field_values(
        payload,
        {"credits", "credits_limit", "credits_used", "credits_remaining", "quota", "requests_remaining", "requests_per_minute"},
    )
    if not quota_values:
        raise ProviderActivationError("account metadata response did not expose quota or credit fields")
    if any(not _nonnegative_number(value) and not isinstance(value, Mapping) for value in quota_values):
        raise ProviderActivationError("account metadata response exposed an invalid quota or credit value")
    nested_quota_values = [
        nested
        for value in quota_values
        if isinstance(value, Mapping)
        for nested in _field_values(value, {"limit", "used", "remaining", "credits", "requests"})
    ]
    if any(not _nonnegative_number(value) for value in nested_quota_values):
        raise ProviderActivationError("account metadata response exposed an invalid nested quota value")


def _aggregate_row_count(value: object) -> int:
    if isinstance(value, list):
        return len(value) + sum(_aggregate_row_count(item) for item in value[:100])
    if isinstance(value, Mapping):
        return sum(_aggregate_row_count(item) for item in value.values())
    return 0


def build_disabled_provider_adapters() -> dict[str, GatedReadOnlyProviderAdapter]:
    """Application-safe registry: no transport and no credentials are loaded."""

    return {provider_id: GatedReadOnlyProviderAdapter(asset) for provider_id, asset in build_existing_provider_assets().items()}
