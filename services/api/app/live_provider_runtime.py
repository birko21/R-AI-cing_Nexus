"""Explicit runtime wiring for owner-configured live provider access.

This module is intentionally separate from application startup.  Importing it
does not read credentials or make a network request.  A caller must opt in with
the provider enable flag, provide credentials through the process environment
or a secret manager, and provide a local approval record for the exact source,
operation and racing code.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

from app.external_provider_integrations import (
    CredentialMaterial,
    GatedReadOnlyProviderAdapter,
    HttpxReadOnlyTransport,
    ProviderActivationError,
    ProviderId,
    ReadOnlyTransport,
    build_existing_provider_assets,
)
from app.source_approval import (
    SourceApprovalRecord,
    evaluate_source_approval,
)


_PROVIDER_TOKENS: dict[str, str] = {
    "formfav": "FORMFAV",
    "punters-edge": "PUNTERS_EDGE",
    "krok-odds": "KROK_ODDS",
    "betfair-exchange": "BETFAIR",
}
_APPROVAL_FIELDS = {
    "written_rights",
    "credential_policy",
    "retention_terms",
    "model_training_permission",
    "display_permission",
    "reconciliation_report",
    "approved_operations",
    "approved_codes",
    "approval_tier",
    "account_entitlement_evidence",
    "credential_custodian",
    "quota_ceiling",
    "kill_switch_reference",
}
_SENSITIVE_APPROVAL_KEYS = {"api_key", "app_key", "session_token", "token", "secret", "password"}


def _env(environ: Mapping[str, str], name: str) -> str | None:
    value = environ.get(name, "").strip()
    return value or None


def _truthy(environ: Mapping[str, str], name: str) -> bool:
    return _env(environ, name) in {"1", "true", "yes", "on"}


def _csv(value: str | None) -> tuple[str, ...]:
    return tuple(item.strip() for item in (value or "").split(",") if item.strip())


def _approval_file(path: str, *, provider_id: str) -> dict[str, Any]:
    approval_path = Path(path).expanduser()
    if not approval_path.is_file():
        raise ProviderActivationError(f"approval file does not exist: {approval_path}")
    try:
        raw = json.loads(approval_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProviderActivationError("approval file is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise ProviderActivationError("approval file must contain a JSON object")
    if any(str(key).lower() in _SENSITIVE_APPROVAL_KEYS for key in raw):
        raise ProviderActivationError("approval file must not contain credentials or secrets")
    unknown = set(raw) - _APPROVAL_FIELDS - {"source_id"}
    if unknown:
        raise ProviderActivationError(f"approval file contains unsupported fields: {','.join(sorted(unknown))}")
    if raw.get("source_id") not in (None, provider_id):
        raise ProviderActivationError("approval file source_id does not match provider")
    return raw


def _approval_from_environment(
    provider_id: str,
    environ: Mapping[str, str],
    *,
    suffix: str = "",
) -> SourceApprovalRecord | None:
    token = _PROVIDER_TOKENS[provider_id]
    prefix = f"NEXUS_PROVIDER_{token}_"
    values: dict[str, Any] = {}
    approval_path = _env(environ, f"{prefix}{suffix}APPROVAL_FILE")
    if approval_path:
        values.update(_approval_file(approval_path, provider_id=provider_id))

    scalar_fields = (
        "written_rights",
        "credential_policy",
        "retention_terms",
        "model_training_permission",
        "display_permission",
        "reconciliation_report",
        "approval_tier",
        "account_entitlement_evidence",
        "credential_custodian",
        "quota_ceiling",
        "kill_switch_reference",
    )
    for field in scalar_fields:
        value = _env(environ, f"{prefix}{suffix}{field.upper()}")
        if value is not None:
            values[field] = value
    for field in ("approved_operations", "approved_codes"):
        value = _env(environ, f"{prefix}{suffix}{field.upper()}")
        if value is not None:
            values[field] = _csv(value)

    if not values:
        return None
    values["source_id"] = provider_id
    try:
        return SourceApprovalRecord(**values)
    except (TypeError, ValueError) as exc:
        raise ProviderActivationError(f"invalid {provider_id} approval configuration") from exc


def _credentials_from_environment(provider_id: str, environ: Mapping[str, str]) -> dict[str, str] | None:
    token = _PROVIDER_TOKENS[provider_id]
    prefix = f"NEXUS_PROVIDER_{token}_"
    if provider_id == "betfair-exchange":
        app_key = _env(environ, f"{prefix}APP_KEY")
        session_token = _env(environ, f"{prefix}SESSION_TOKEN")
        return {"app_key": app_key, "session_token": session_token} if app_key and session_token else None
    api_key = _env(environ, f"{prefix}API_KEY")
    return {"api_key": api_key} if api_key else None


@dataclass(frozen=True)
class LiveProviderConfig:
    provider_id: ProviderId
    enabled: bool
    diagnostics_enabled: bool
    credentials: Mapping[str, str] | None
    approval: SourceApprovalRecord | None
    diagnostic_approvals: Mapping[str, SourceApprovalRecord]

    def status(self) -> dict[str, object]:
        checkpoint = evaluate_source_approval(self.approval) if self.approval else None
        return {
            "provider": self.provider_id,
            "enabled": self.enabled,
            "credentials_configured": bool(self.credentials),
            "diagnostics_enabled": self.diagnostics_enabled,
            "approval_status": checkpoint.status if checkpoint else "NOT_CONFIGURED",
            "approval_missing_requirements": list(checkpoint.missing_requirements) if checkpoint else ["approval_record"],
            "diagnostic_approval_tiers": sorted(self.diagnostic_approvals),
        }


@dataclass
class LiveProviderHandle:
    config: LiveProviderConfig
    adapter: GatedReadOnlyProviderAdapter
    transport: ReadOnlyTransport

    def close(self) -> None:
        close = getattr(self.transport, "close", None)
        if callable(close):
            close()


def load_live_provider_config(provider_id: str, *, environ: Mapping[str, str] | None = None) -> LiveProviderConfig:
    if provider_id not in _PROVIDER_TOKENS:
        raise ProviderActivationError(f"unknown provider: {provider_id}")
    values = os.environ if environ is None else environ
    return LiveProviderConfig(
        provider_id=provider_id,  # type: ignore[arg-type]
        enabled=_truthy(values, f"NEXUS_PROVIDER_{_PROVIDER_TOKENS[provider_id]}_ENABLED"),
        diagnostics_enabled=_truthy(values, "NEXUS_DIAGNOSTICS_ENABLED"),
        credentials=_credentials_from_environment(provider_id, values),
        approval=_approval_from_environment(provider_id, values),
        diagnostic_approvals={
            tier.approval_tier: tier
            for tier in (
                _approval_from_environment(provider_id, values, suffix="ACCOUNT_METADATA_"),
                _approval_from_environment(provider_id, values, suffix="DIAGNOSTIC_"),
            )
            if tier is not None and tier.approval_tier is not None
        },
    )


def build_live_provider_handle(
    provider_id: str,
    *,
    environ: Mapping[str, str] | None = None,
    transport: ReadOnlyTransport | None = None,
) -> LiveProviderHandle:
    config = load_live_provider_config(provider_id, environ=environ)
    if not config.enabled:
        raise ProviderActivationError(f"{provider_id} is disabled; set its explicit NEXUS provider enable flag")
    if not config.credentials:
        raise ProviderActivationError(f"{provider_id} credentials are not configured in the process environment")
    selected_transport = transport or HttpxReadOnlyTransport()

    def resolve() -> CredentialMaterial:
        assert config.credentials is not None
        return dict(config.credentials)

    adapter = GatedReadOnlyProviderAdapter(
        build_existing_provider_assets()[provider_id],
        transport=selected_transport,
        credential_resolver=resolve,
    )
    return LiveProviderHandle(config=config, adapter=adapter, transport=selected_transport)


def configured_provider_status(*, environ: Mapping[str, str] | None = None) -> tuple[dict[str, object], ...]:
    values = os.environ if environ is None else environ
    return tuple(load_live_provider_config(provider_id, environ=values).status() for provider_id in _PROVIDER_TOKENS)
