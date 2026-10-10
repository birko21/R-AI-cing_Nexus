from __future__ import annotations

import hmac
import os
from collections.abc import Callable

from fastapi import Header, HTTPException


LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


def _is_true(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def validate_bind_configuration() -> None:
    host = os.environ.get("API_HOST", "127.0.0.1")
    app_env = os.environ.get("APP_ENV", "development")
    allow_local_auth = _is_true(os.environ.get("ALLOW_LOCAL_AUTH"))
    oidc_issuer = os.environ.get("OIDC_ISSUER")
    oidc_audience = os.environ.get("OIDC_AUDIENCE")
    oidc_configured = bool(oidc_issuer and oidc_audience)

    if host not in LOOPBACK_HOSTS and not oidc_configured:
        raise RuntimeError("External API binds require approved OIDC configuration")
    if app_env != "development" and not oidc_configured:
        raise RuntimeError("Non-development API environments require approved OIDC configuration")
    if allow_local_auth and (app_env != "development" or host not in LOOPBACK_HOSTS):
        raise RuntimeError("Local authentication is permitted only on a development loopback bind")


def _configured_local_token() -> str | None:
    token = os.environ.get("LOCAL_AUTH_TOKEN")
    if not token or token.startswith("replace-with-"):
        return None
    return token


def require_scopes(*required_scopes: str) -> Callable:
    def dependency(authorization: str | None = Header(default=None)) -> dict[str, object]:
        validate_bind_configuration()
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="bearer authentication is required")

        if not _is_true(os.environ.get("ALLOW_LOCAL_AUTH")):
            raise HTTPException(status_code=401, detail="owner authentication is not enabled")

        configured_token = _configured_local_token()
        supplied_token = authorization.removeprefix("Bearer ").strip()
        if configured_token is None or not hmac.compare_digest(supplied_token, configured_token):
            raise HTTPException(status_code=401, detail="bearer token is invalid")

        configured_scopes = {
            scope.strip() for scope in os.environ.get("LOCAL_AUTH_SCOPES", "").split(",") if scope.strip()
        }
        missing = sorted(set(required_scopes) - configured_scopes)
        if missing:
            raise HTTPException(status_code=403, detail=f"required scope is missing: {', '.join(missing)}")
        return {"subject": "local-owner", "scopes": sorted(configured_scopes)}

    return dependency


races_read = require_scopes("races:read")
forecasts_read = require_scopes("forecasts:read")
selections_read = require_scopes("selections:read")
selections_write = require_scopes("selections:write")


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    """Compatibility dependency retained for callers that only need bearer presence."""

    require_scopes()(authorization)
