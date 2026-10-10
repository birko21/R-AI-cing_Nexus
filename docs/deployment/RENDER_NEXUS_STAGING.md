# R-AI-cing Nexus Render staging

Status: **Blueprint prepared and validated; Render resources not provisioned**

This deployment is intentionally independent of The Long Straight. It uses
only the Nexus repository and Nexus-specific service names:

- nexus-staging-api — free Python web service running FastAPI.
- nexus-staging-frontend — free Render static site serving the Vite build.

No existing Render service, environment variable, secret, deployment or
repository outside Nexus is referenced or modified.

## Architecture and data decision

The current API uses an in-memory selection journal, synthetic fixtures and no
database connection during application startup. A database is therefore not
necessary for this staging foundation. No Postgres, Key Value, worker, cron,
persistent disk or paid resource is declared in render.yaml.

This decision must be revisited before any durable user data, provider payload,
historical result, model-training artifact or multi-instance workload is
introduced. Free Render filesystems are ephemeral and are not a persistence
mechanism.

## Authentication and authorization

Local bearer authentication remains available only for loopback development.
The Render API service is configured with:

- AUTH_MODE=oidc
- API_HOST=0.0.0.0
- ALLOW_LOCAL_AUTH=false
- HTTPS OIDC_ISSUER, OIDC_AUDIENCE and OIDC_JWKS_URL

The backend validates the JWT signature against the configured JWKS, then
requires issuer, audience, expiry, issued-at time, subject and route scopes.
Only RS256, RS384 and RS512 are accepted. JWKS responses are cached briefly
and refreshed when a signing key rotates. Authentication failures do not
return token contents.

The Blueprint leaves OIDC values as sync: false; the owner must enter them
in the Nexus service only. OIDC configuration is not considered complete until
the issuer, audience, JWKS endpoint, token signature and required scopes have
been tested against the real identity provider.

The frontend is fail-closed when VITE_AUTH_REQUIRED=true and shows only a
protected-configuration screen. It is not approved for public research access
until its OIDC login flow, callback and protected session are supplied and
verified. The Blueprint therefore sets both services to autoDeployTrigger: off;
creating the Blueprint must not be treated as authorization to expose the
research application.

## Provider isolation

The following Nexus-only variables are reserved for future, separately
approved configuration:

| Provider | Enable flag | Credential variables |
|---|---|---|
| PuntersEdge | NEXUS_PROVIDER_PUNTERS_EDGE_ENABLED | NEXUS_PROVIDER_PUNTERS_EDGE_API_KEY |
| FormFav | NEXUS_PROVIDER_FORMFAV_ENABLED | NEXUS_PROVIDER_FORMFAV_API_KEY |
| Krok Odds | NEXUS_PROVIDER_KROK_ODDS_ENABLED | NEXUS_PROVIDER_KROK_ODDS_API_KEY |
| Betfair | NEXUS_PROVIDER_BETFAIR_ENABLED | NEXUS_PROVIDER_BETFAIR_APP_KEY, NEXUS_PROVIDER_BETFAIR_SESSION_TOKEN |

All enable flags and NEXUS_DIAGNOSTICS_ENABLED default to false. No
provider request is made by this infrastructure work. The existing three-tier
approval gate remains in the application and the owner's Tier 1 authorization
for one PuntersEdge account-metadata request is preserved; it is not executed
here. Historical results/form access, retention, model training, Betfair
market operations, wagering and trading remain blocked.

## Cost and free-tier guardrails

The Blueprint uses two free services, disables automatic deploys, adds no
database, and does not enable paid scaling. Render's current free-tier
limitations include 750 free web-service instance hours per workspace per
calendar month, 15-minute idle spin-down, ephemeral filesystems, and shared
bandwidth/build-pipeline allowances. Static sites are free but still consume
workspace bandwidth and build-pipeline allowances.

Official references checked 10 October 2026:

- https://render.com/docs/free
- https://render.com/docs/blueprint-spec
- https://render.com/docs/health-checks

The owner must confirm the workspace's remaining included usage and spend
limit before applying the Blueprint. No payment method, upgrade, paid plan or
automatic spend is requested by this change.

## Apply runbook

1. Confirm the Render workspace is My Workspace and that the target repository
   is https://github.com/birko21/R-AI-cing_Nexus.
2. Review render.yaml and run python scripts/validate_render_blueprint.py.
3. In Render, create a new Blueprint named r-ai-cing-nexus-staging.
4. Confirm the two proposed services are Nexus-only, both deployment triggers
   are manual, both plans are free, and no database is proposed.
5. Before any deploy, enter OIDC issuer, audience and JWKS URL for the
   approved identity provider. Do not enter provider keys yet.
6. Complete the OIDC integration test with a real signed token:
   - valid token with races:read reaches a protected route;
   - wrong issuer, audience, signature, expiry or scope is rejected;
   - local bearer auth is rejected in staging;
   - /health/live remains an unauthenticated liveness check only.
7. Set VITE_API_BASE_URL only after the API hostname is known. Do not
   enable provider flags.
8. Deploy manually only after CI is green and independent review is complete.
   Verify /health/live, protected-route denial, protected-route success and
   synthetic-only /v1/system/status.
9. Use Render's deploy history to roll back to the previous successful deploy
   if health checks or authentication tests fail. Do not use a rollback to
   bypass a failed review or security gate.

## Current owner actions

- Retain the verified Render CLI access for My Workspace and re-check the
  workspace before any future apply.
- Supply a real OIDC issuer, audience, JWKS URL and redirect/callback details.
- Independently review the authentication and Blueprint PR before merge.
- Decide whether a protected frontend OIDC client is available; otherwise keep
  the Blueprint unapplied.
- Confirm free-tier usage and spend-limit settings.
- Enter provider credentials only in the separate Nexus Render environment,
  after each provider's own approval record is complete.
