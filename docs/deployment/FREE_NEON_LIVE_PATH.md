# Free live-provider deployment path

Use the existing free Render web service for the API, Neon Free for
PostgreSQL, and GitHub Actions for the bounded schedule. This avoids Render
Postgres and Render Cron resources.

## Secret wiring

In `nexus-staging-api`, add these values without committing or displaying
them:

- `DATABASE_URL`: Neon pooled connection string for API traffic.
- `DATABASE_URL_UNPOOLED`: Neon direct connection string for Alembic.
- `NEXUS_INGESTION_TRIGGER_TOKEN`: a new random bearer token.
- `NEXUS_PROVIDER_PUNTERS_EDGE_API_KEY`: existing Render secret.

Add the same trigger token to the GitHub repository secret
`NEXUS_INGESTION_TRIGGER_TOKEN`, plus
`NEXUS_INGESTION_URL=https://nexus-staging-api-feap.onrender.com`.

The workflow does not receive the provider API key or database URL. The
provider call and database write stay inside the Render API service.

## Non-secret live configuration

Set the API service to:

```text
NEXUS_API_PERSISTENCE=postgres
NEXUS_DATA_MODE=LICENSED
NEXUS_LIVE_PROVIDER=punters-edge
NEXUS_LIVE_OPERATIONS=GET_RESULTS
NEXUS_LIVE_CODES=THOROUGHBRED
NEXUS_LIVE_OPERATION=GET_RESULTS
NEXUS_LIVE_CODE=THOROUGHBRED
NEXUS_LIVE_READ_ONLY=true
NEXUS_PROVIDER_PUNTERS_EDGE_ENABLED=true
NEXUS_DIAGNOSTICS_ENABLED=false
```

Also enter the non-secret private read approval fields required by the
provider gate. Keep other providers disabled.

## Schema and first run

1. Run Alembic once with `DATABASE_URL_UNPOOLED` against a Neon branch.
2. Deploy the API with both Neon URLs configured.
3. Merge `.github/workflows/live-provider-ingestion.yml` to the repository's
   default branch; GitHub scheduled workflows do not run from a feature branch.
4. Trigger the workflow manually once and verify only the safe success
   counters, canonical rows, and `wagering_enabled=false`.

The endpoint is hidden from OpenAPI and requires the dedicated trigger token.
It returns no provider payload, credentials, runner prices, or raw errors.
