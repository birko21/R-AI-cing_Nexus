"""Validate the Nexus Render Blueprint without contacting Render or providers."""

from __future__ import annotations

from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "render.yaml"
EXPECTED_SERVICES = {"nexus-staging-api", "nexus-staging-frontend", "nexus-staging-live-ingestion"}
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
    databases = document.get("databases")
    require(isinstance(databases, list) and len(databases) == 1, "Blueprint must define the Nexus staging database")
    database = databases[0]
    require(database.get("name") == "nexus-staging-db", "database must use the Nexus staging name")
    require(database.get("region") == "singapore", "database must be colocated with the API")

    services = document.get("services")
    require(isinstance(services, list) and len(services) == 3, "Blueprint must define exactly three staging services")
    by_name = {service.get("name"): service for service in services if isinstance(service, dict)}
    require(set(by_name) == EXPECTED_SERVICES, "Blueprint service names must be Nexus-specific")

    api = by_name["nexus-staging-api"]
    require(api.get("type") == "web" and api.get("runtime") == "python", "API must be a Python web service")
    require(api.get("plan") == "free", "API must remain on the free plan")
    require(api.get("healthCheckPath") == "/health/live", "API health check must use /health/live")
    require("alembic" in str(api.get("preDeployCommand")), "API must run database migrations before deploy")
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
    require(api_env.get("DATABASE_URL", {}).get("fromDatabase", {}).get("name") == "nexus-staging-db", "API must use the internal staging database")
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
    ingestion = by_name["nexus-staging-live-ingestion"]
    require(ingestion.get("type") == "cron" and ingestion.get("runtime") == "python", "live ingestion must be a Python cron service")
    require(ingestion.get("schedule") == "0 * * * *", "live ingestion must run hourly in UTC")
    require("run_live_provider_ingestion.py" in str(ingestion.get("startCommand")), "cron must run the live ingestion runner")
    ingestion_env = env_map(ingestion)
    require(ingestion_env.get("DATABASE_URL", {}).get("fromDatabase", {}).get("name") == "nexus-staging-db", "cron must use the internal staging database")
    require(ingestion_env.get("NEXUS_LIVE_PROVIDER", {}).get("value") == "punters-edge", "cron must start with PuntersEdge")
    print("RENDER BLUEPRINT PASS: OIDC-gated API, PostgreSQL, owner-scoped PuntersEdge cron ingestion, synthetic runtime removed")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"RENDER BLUEPRINT FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
