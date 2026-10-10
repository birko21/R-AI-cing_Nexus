"""Validate the Nexus Render Blueprint without contacting Render or providers."""

from __future__ import annotations

from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "render.yaml"
EXPECTED_SERVICES = {"nexus-staging-api", "nexus-staging-frontend"}
PROVIDER_FLAGS = (
    "NEXUS_PROVIDER_PUNTERS_EDGE_ENABLED",
    "NEXUS_PROVIDER_FORMFAV_ENABLED",
    "NEXUS_PROVIDER_KROK_ODDS_ENABLED",
    "NEXUS_PROVIDER_BETFAIR_ENABLED",
)


def env_map(service: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(item["key"]): item
        for item in service.get("envVars", [])
        if isinstance(item, dict) and "key" in item
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    require(BLUEPRINT.is_file(), "render.yaml is missing")
    document = yaml.safe_load(BLUEPRINT.read_text(encoding="utf-8"))
    require(isinstance(document, dict), "render.yaml must contain a mapping")
    require(not document.get("databases"), "Nexus staging must not provision a database yet")

    services = document.get("services")
    require(isinstance(services, list) and len(services) == 2, "Blueprint must define exactly two staging services")
    by_name = {service.get("name"): service for service in services if isinstance(service, dict)}
    require(set(by_name) == EXPECTED_SERVICES, "Blueprint service names must be Nexus-specific")

    api = by_name["nexus-staging-api"]
    require(api.get("type") == "web" and api.get("runtime") == "python", "API must be a Python web service")
    require(api.get("plan") == "free", "API must remain on the free plan")
    require(api.get("healthCheckPath") == "/health/live", "API health check must use /health/live")
    require(api.get("autoDeployTrigger") == "off", "API auto-deploy must remain disabled")
    require("0.0.0.0" in str(api.get("startCommand")) and "$PORT" in str(api.get("startCommand")), "API must bind Render's PORT on all interfaces")
    api_env = env_map(api)
    require(api_env.get("AUTH_MODE", {}).get("value") == "oidc", "staging API must use OIDC")
    require(api_env.get("ALLOW_LOCAL_AUTH", {}).get("value") in {False, "false"}, "local bearer auth must be disabled")
    for key in ("OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URL"):
        require(api_env.get(key, {}).get("sync") is False, f"{key} must be entered as a Render secret/config value")
    require(api_env.get("NEXUS_DIAGNOSTICS_ENABLED", {}).get("value") in {False, "false"}, "diagnostics must be disabled")
    for key in PROVIDER_FLAGS:
        require(api_env.get(key, {}).get("value") in {False, "false"}, f"{key} must default to false")
    for item in api_env.values():
        if str(item.get("key", "")).endswith(("_API_KEY", "_APP_KEY", "_SESSION_TOKEN")):
            require(item.get("sync") is False, f"provider secret {item['key']} must never be committed")

    frontend = by_name["nexus-staging-frontend"]
    require(frontend.get("type") == "web" and frontend.get("runtime") == "static", "frontend must be a static site")
    require(frontend.get("autoDeployTrigger") == "off", "frontend auto-deploy must remain disabled")
    require(frontend.get("staticPublishPath") == "apps/web/dist", "frontend must publish the Vite dist directory")
    routes = frontend.get("routes", [])
    require(any(isinstance(route, dict) and route.get("type") == "rewrite" and route.get("source") == "/*" and route.get("destination") == "/index.html" for route in routes), "frontend must have an SPA fallback")
    print("RENDER BLUEPRINT PASS: Nexus-only, free-plan, OIDC-gated, provider-disabled staging configuration")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"RENDER BLUEPRINT FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
