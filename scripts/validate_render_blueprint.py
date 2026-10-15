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
    require("databases" not in document, "free Blueprint must not create a Render database")

    services = document.get("services")
    require(isinstance(services, list) and len(services) == 2, "free Blueprint must define exactly two staging services")
    by_name = {service.get("name"): service for service in services if isinstance(service, dict)}
    require(set(by_name) == EXPECTED_SERVICES, "Blueprint service names must be Nexus-specific")

    api = by_name["nexus-staging-api"]
    require(api.get("type") == "web" and api.get("runtime") == "python", "API must be a Python web service")
    require(api.get("plan") == "free", "API must remain on the free plan")
    require(api.get("healthCheckPath") == "/health/live", "API health check must use /health/live")
    require("alembic" in str(api.get("preDeployCommand")) and "DATABASE_URL_UNPOOLED" in str(api.get("preDeployCommand")), "API must run migrations with the direct Neon URL")
    require(api.get("autoDeployTrigger") == "off", "API auto-deploy must remain disabled")
    require("0.0.0.0" in str(api.get("startCommand")) and "$PORT" in str(api.get("startCommand")), "API must bind Render's PORT on all interfaces")
    api_env = env_map(api)
    require(api_env.get("AUTH_MODE", {}).get("value") == "oidc", "staging API must use OIDC")
    require(api_env.get("ALLOW_LOCAL_AUTH", {}).get("value") in {False, "false"}, "local bearer auth must be disabled")
    for key in ("OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URL"):
        require(api_env.get(key, {}).get("sync") is False, f"{key} must be entered as a Render secret/config value")
    require(api_env.get("OIDC_ALLOWED_SUBJECTS", {}).get("sync") is False, "owner subject allowlist must be entered as a Render config value")
    cors = str(api_env.get("CORS_ALLOWED_ORIGINS", {}).get("value", ""))
    require(cors == "https://nexus-staging-frontend.onrender.com" and "*" not in cors, "API CORS must strictly allow the Nexus frontend origin")
    require(api_env.get("NEXUS_DIAGNOSTICS_ENABLED", {}).get("value") in {False, "false"}, "diagnostics must be disabled")
    require(api_env.get("NEXUS_DATA_MODE", {}).get("value") == "LICENSED", "staging API must use licensed data mode")
    require(api_env.get("NEXUS_API_PERSISTENCE", {}).get("value") == "postgres", "staging API must use PostgreSQL persistence")
    require(api_env.get("NEXUS_LIVE_PROVIDER", {}).get("value") == "punters-edge", "staging must start with PuntersEdge")
    require(api_env.get("DATABASE_URL", {}).get("sync") is False, "API must accept the pooled Neon URL as a Render secret")
    require(api_env.get("DATABASE_URL_UNPOOLED", {}).get("sync") is False, "API must accept the direct Neon URL as a Render secret")
    require(api_env.get("NEXUS_INGESTION_TRIGGER_TOKEN", {}).get("sync") is False, "ingestion trigger token must remain a Render secret")
    require(api_env.get("NEXUS_PROVIDER_PUNTERS_EDGE_ENABLED", {}).get("value") in {True, "true"}, "PuntersEdge must be enabled for the first live lane")
    for key in PROVIDER_FLAGS[1:]:
        require(api_env.get(key, {}).get("value") in {False, "false"}, f"{key} must remain disabled")
    for item in api_env.values():
        if str(item.get("key", "")).endswith(("_API_KEY", "_APP_KEY", "_SESSION_TOKEN")):
            require(item.get("sync") is False, f"provider secret {item['key']} must never be committed")

    frontend = by_name["nexus-staging-frontend"]
    require(frontend.get("type") == "web" and frontend.get("runtime") == "static", "frontend must be a static site")
    require(frontend.get("autoDeployTrigger") == "off", "frontend auto-deploy must remain disabled")
    require(frontend.get("staticPublishPath") == "apps/web/dist", "frontend must publish the Vite dist directory")
    frontend_env = env_map(frontend)
    require(frontend_env.get("VITE_API_BASE_URL", {}).get("value") == "https://nexus-staging-api-feap.onrender.com", "frontend must use the Nexus staging API URL")
    for key in ("VITE_AUTH0_DOMAIN", "VITE_AUTH0_CLIENT_ID", "VITE_AUTH0_AUDIENCE", "VITE_AUTH0_ALLOWED_SUBJECT"):
        require(frontend_env.get(key, {}).get("sync") is False, f"{key} must be configured separately in Render")
    routes = frontend.get("routes", [])
    require(any(isinstance(route, dict) and route.get("type") == "rewrite" and route.get("source") == "/*" and route.get("destination") == "/index.html" for route in routes), "frontend must have an SPA fallback")
    headers = frontend.get("headers", [])
    csp = " ".join(str(item.get("value", "")) for item in headers if isinstance(item, dict) and item.get("name") == "Content-Security-Policy")
    require("https://dev-raicingnexus.au.auth0.com" in csp and "https://nexus-staging-api-feap.onrender.com" in csp, "frontend CSP must allow the configured Auth0 tenant and Nexus API")
    workflow = ROOT / ".github" / "workflows" / "live-provider-ingestion.yml"
    require(workflow.is_file(), "free deployment must provide a GitHub Actions ingestion schedule")
    workflow_text = workflow.read_text(encoding="utf-8")
    require("17 * * * *" in workflow_text and "/internal/live-ingestion/run" in workflow_text, "GitHub Actions must trigger the protected hourly ingestion endpoint")
    print("RENDER BLUEPRINT PASS: OIDC-gated API, Neon PostgreSQL, protected GitHub Actions ingestion, synthetic runtime removed")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"RENDER BLUEPRINT FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
