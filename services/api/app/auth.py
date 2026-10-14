from __future__ import annotations

import hmac
import json
import logging
import os
import threading
import time
from collections.abc import Callable, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import jwt
from fastapi import Header, HTTPException


LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
OIDC_ALGORITHMS = ("RS256", "RS384", "RS512")
JWKS_CACHE_SECONDS = 300
_jwks_cache: tuple[float, tuple[Mapping[str, object], ...]] | None = None
_jwks_lock = threading.Lock()
logger = logging.getLogger(__name__)


def _is_true(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _auth_mode() -> str:
    return os.environ.get("AUTH_MODE", "local").strip().lower()


def _oidc_settings() -> tuple[str, str, str]:
    # Auth0 publishes and signs tokens with the canonical trailing-slash issuer.
    # Keep the configured issuer exact so PyJWT performs strict claim validation.
    issuer = os.environ.get("OIDC_ISSUER", "").strip()
    audience = os.environ.get("OIDC_AUDIENCE", "").strip()
    jwks_url = os.environ.get("OIDC_JWKS_URL", "").strip()
    if not issuer or not audience or not jwks_url:
        raise RuntimeError("OIDC requires OIDC_ISSUER, OIDC_AUDIENCE and OIDC_JWKS_URL")
    return issuer, audience, jwks_url


def _oidc_allowed_subjects() -> frozenset[str]:
    return frozenset(item.strip() for item in os.environ.get("OIDC_ALLOWED_SUBJECTS", "").split(",") if item.strip())


def _validate_oidc_settings(*, require_https: bool) -> None:
    issuer, _, jwks_url = _oidc_settings()
    for name, value in (("OIDC_ISSUER", issuer), ("OIDC_JWKS_URL", jwks_url)):
        parsed = urlparse(value)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise RuntimeError(f"{name} must be an absolute URL")
        if require_https and parsed.scheme != "https":
            raise RuntimeError(f"{name} must use HTTPS outside loopback development")
    if not _oidc_allowed_subjects():
        raise RuntimeError("OIDC_ALLOWED_SUBJECTS must explicitly allow the owner identity")


def validate_bind_configuration() -> None:
    host = os.environ.get("API_HOST", "127.0.0.1")
    app_env = os.environ.get("APP_ENV", "development")
    allow_local_auth = _is_true(os.environ.get("ALLOW_LOCAL_AUTH"))
    mode = _auth_mode()
    loopback = host in LOOPBACK_HOSTS

    if mode not in {"local", "oidc"}:
        raise RuntimeError("AUTH_MODE must be local or oidc")
    if mode == "local":
        if not loopback:
            raise RuntimeError("External API binds require approved OIDC configuration")
        if app_env != "development":
            raise RuntimeError("Non-development API environments require approved OIDC configuration")
        return

    _validate_oidc_settings(require_https=not loopback or app_env != "development")
    if allow_local_auth:
        raise RuntimeError("ALLOW_LOCAL_AUTH cannot be enabled with OIDC authentication")


def _configured_local_token() -> str | None:
    token = os.environ.get("LOCAL_AUTH_TOKEN")
    if not token or token.startswith("replace-with-"):
        return None
    return token


def _configured_scopes() -> set[str]:
    return {scope.strip() for scope in os.environ.get("LOCAL_AUTH_SCOPES", "").split(",") if scope.strip()}


def _fetch_jwks() -> tuple[Mapping[str, object], ...]:
    _, _, jwks_url = _oidc_settings()
    request = Request(jwks_url, headers={"Accept": "application/json", "User-Agent": "r-ai-cing-nexus-auth/1"})
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310 - URL is owner-configured OIDC metadata.
            if response.status != 200:
                raise RuntimeError("OIDC JWKS endpoint did not return 200")
            document = json.load(response)
    except Exception as exc:  # pragma: no cover - network failures are exercised through the validation boundary.
        raise RuntimeError("OIDC signing-key retrieval failed") from exc
    keys = document.get("keys") if isinstance(document, dict) else None
    if not isinstance(keys, list) or not keys or not all(isinstance(item, dict) for item in keys):
        raise RuntimeError("OIDC JWKS document is invalid")
    return tuple(keys)


def _jwks(force_refresh: bool = False) -> tuple[Mapping[str, object], ...]:
    global _jwks_cache
    now = time.monotonic()
    with _jwks_lock:
        if not force_refresh and _jwks_cache and now - _jwks_cache[0] < JWKS_CACHE_SECONDS:
            return _jwks_cache[1]
        keys = _fetch_jwks()
        _jwks_cache = (now, keys)
        return keys


def _signing_key(token: str) -> tuple[object, str]:
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg")
    key_id = header.get("kid")
    if algorithm not in OIDC_ALGORITHMS or not isinstance(key_id, str) or not key_id:
        raise ValueError("unsupported OIDC token header")
    for keys in (_jwks(), _jwks(force_refresh=True)):
        for jwk in keys:
            if jwk.get("kid") == key_id:
                return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk)), algorithm
    raise ValueError("OIDC signing key was not found")


def _token_scopes(claims: Mapping[str, object]) -> set[str]:
    scope_claim = claims.get("scope")
    scopes = set(scope_claim.split()) if isinstance(scope_claim, str) else set()
    scp_claim = claims.get("scp")
    if isinstance(scp_claim, list):
        scopes.update(item for item in scp_claim if isinstance(item, str))
    permissions_claim = claims.get("permissions")
    if isinstance(permissions_claim, list):
        scopes.update(item for item in permissions_claim if isinstance(item, str))
    return scopes


class OwnerIdentityNotAllowed(PermissionError):
    """Raised when a valid token is not for the explicitly allowlisted owner."""


def _oidc_reason_code(error: BaseException) -> str:
    """Return a safe diagnostic code without including token or claim contents."""

    if isinstance(error, OwnerIdentityNotAllowed):
        return "owner_not_allowlisted"
    if isinstance(error, PermissionError):
        return "missing_scope"
    if isinstance(error, jwt.ExpiredSignatureError):
        return "token_expired"
    if isinstance(error, jwt.InvalidIssuerError):
        return "issuer_mismatch"
    if isinstance(error, jwt.InvalidAudienceError):
        return "audience_mismatch"
    if isinstance(error, jwt.InvalidSignatureError):
        return "signature_invalid"
    if isinstance(error, jwt.MissingRequiredClaimError):
        return "required_claim_missing"
    return "invalid_token"


def _validate_oidc_bearer(token: str, required_scopes: tuple[str, ...]) -> dict[str, object]:
    issuer, audience, _ = _oidc_settings()
    key, algorithm = _signing_key(token)
    claims = jwt.decode(
        token,
        key,
        algorithms=[algorithm],
        audience=audience,
        issuer=issuer,
        options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise ValueError("OIDC subject is missing")
    if subject not in _oidc_allowed_subjects():
        raise OwnerIdentityNotAllowed("owner identity is not allowlisted")
    scopes = _token_scopes(claims)
    missing = sorted(set(required_scopes) - scopes)
    if missing:
        raise PermissionError(", ".join(missing))
    return {"subject": subject, "scopes": sorted(scopes), "issuer": issuer}


def require_scopes(*required_scopes: str) -> Callable:
    def dependency(authorization: str | None = Header(default=None)) -> dict[str, object]:
        try:
            validate_bind_configuration()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail="authentication is not configured") from exc
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="bearer authentication is required")
        supplied_token = authorization.removeprefix("Bearer ").strip()
        if not supplied_token:
            raise HTTPException(status_code=401, detail="bearer authentication is required")

        if _auth_mode() == "oidc":
            try:
                return _validate_oidc_bearer(supplied_token, required_scopes)
            except OwnerIdentityNotAllowed as exc:
                logger.warning("OIDC authentication rejected reason=%s", _oidc_reason_code(exc))
                raise HTTPException(status_code=403, detail="owner identity is not allowlisted") from exc
            except PermissionError as exc:
                logger.warning("OIDC authentication rejected reason=%s", _oidc_reason_code(exc))
                raise HTTPException(status_code=403, detail=f"required scope is missing: {exc}") from exc
            except Exception as exc:
                logger.warning("OIDC authentication rejected reason=%s", _oidc_reason_code(exc))
                raise HTTPException(status_code=401, detail="OIDC bearer token is invalid") from exc

        configured_token = _configured_local_token()
        if configured_token is None or not hmac.compare_digest(supplied_token, configured_token):
            raise HTTPException(status_code=401, detail="bearer token is invalid")
        configured_scopes = _configured_scopes()
        missing = sorted(set(required_scopes) - configured_scopes)
        if missing:
            raise HTTPException(status_code=403, detail=f"required scope is missing: {', '.join(missing)}")
        return {"subject": "local-owner", "scopes": sorted(configured_scopes)}

    return dependency


races_read = require_scopes("races:read")
forecasts_read = require_scopes("forecasts:read")
selections_read = require_scopes("selections:read")
selections_write = require_scopes("selections:write")
providers_read = require_scopes("providers:read")


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    """Compatibility dependency retained for callers that only need bearer presence."""

    require_scopes()(authorization)
