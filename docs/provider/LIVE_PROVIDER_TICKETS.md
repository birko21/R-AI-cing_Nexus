# Live provider migration tickets

The live lane is private, read-only, owner-scoped, and wagering-disabled.
Synthetic fixtures remain valid for CI and local development; they are not a
runtime fallback for a licensed deployment.

## LIVE-001 — Define private live-provider scope — COMPLETE

The runtime accepts an explicit provider, operation, racing-code, and
read-only scope through `NEXUS_LIVE_*` configuration. A private single-owner
read tier is supported without implying historical retention or model-training
permission.

## LIVE-002 — Add live runtime/status controls — COMPLETE

`NEXUS_DATA_MODE=LICENSED` requires PostgreSQL, an explicit provider scope,
and read-only mode. System status exposes only non-secret provider metadata.

## LIVE-003 — Add a bounded live probe — COMPLETE

The authenticated `POST /v1/provider-probes/punters-edge` route performs the
bounded diagnostic flow and returns aggregate diagnostics only. It rejects
unauthenticated access and does not retain raw provider payloads.

## LIVE-004 — Project approved envelopes into canonical tables — COMPLETE

Approved provider envelopes pass through strict identity and timestamp
validation before canonical meetings, races, entries, and official results
are written. Ambiguous records are rejected rather than guessed.

## LIVE-005 — Wire PostgreSQL and migrations — COMPLETE

The Alembic chain and transactional live-ingestion runner are ready. The
`nexus-staging` Neon project and `production` branch are now linked. The
pooled and direct URLs are available through the ignored local `.env.local`,
all 19 migrations have been applied, and the API uses the installed psycopg 3
driver. The Render service uses the Neon URLs as secrets; Render does not
create a paid database resource.

## LIVE-006 — Wire Render runtime secrets — COMPLETE

The pooled and direct Neon URLs, existing PuntersEdge API key, generated
ingestion trigger token, and licensed read-only scope are configured in
`nexus-staging-api`. Provider credentials and database URLs remain in Render.

## LIVE-007 — Add scheduled ingestion — COMPLETE

The protected `/internal/live-ingestion/run` endpoint performs one bounded
read using provider credentials held in Render. A GitHub Actions schedule
triggers it hourly, avoiding Render's paid Cron service. Each run persists the
approved receipt/envelope, projects canonical data, and exits without placing
orders or wagers.

## LIVE-008 — Remove synthetic runtime fallback — COMPLETE

Synthetic repositories remain available only for local/test mode. A licensed
deployment fails closed unless PostgreSQL and the explicit live scope are
configured. The staging Render service is now licensed and provider-backed;
synthetic fixtures remain confined to local/test paths.

## LIVE-009 — Deploy and validate on Render — COMPLETE

The existing free API service is live and health-checked. Final validation
reports licensed mode, Neon/Postgres persistence, the enabled PuntersEdge
provider, and wagering disabled. The protected ingestion endpoint rejects
unauthenticated requests.

## LIVE-010 — Verify canonical persistence and idempotency — COMPLETE

Three bounded runs were executed. The first successful run created the receipt,
envelope, and canonical rows. After correcting result identity to use the race
field revision, the repeat run returned zero new canonical results; meetings,
races, participants, and entries remained deduplicated. The database retains
one pre-fix legacy result row plus the current canonical result row.

## LIVE-011 — Operational closeout — COMPLETE

Record the safe response shape, failure behavior, kill-switch procedure, and
rollback steps. Confirm that provider failures fail closed and that the API
never exposes raw payloads, credentials, or wagering operations. The provider
enable flag is the kill switch; disabling it causes the runner to fail closed.
The rollback target is the previous known-good Render deploy for staging.

## LIVE-012 — Show licensed meetings in the dashboard — COMPLETE

The frontend reads the runtime mode and canonical meeting page. In licensed
mode it displays provider-backed meetings with a `LIVE READ-ONLY` state and
does not render the synthetic assistant or synthetic research cards.

## LIVE-013 — Expose canonical races by meeting — COMPLETE

The API provides an authenticated, paginated
`GET /v1/meetings/{meeting_id}/races` route backed by both synthetic local
fixtures and the PostgreSQL canonical repository. The OpenAPI contract,
pagination, as-of filtering, and Neon-backed licensed response are verified.

## LIVE-014 — Show licensed race and entry detail — COMPLETE

The frontend live meeting view loads canonical races and entries through the
scoped API, displays field revision/status and source receipt identifiers, and
fails closed when detail is unavailable. Forecasts, market data and synthetic
replacement values are not shown in this licensed view.

## Current external gate

The free path is active. Neon supplies the database, Render supplies the free
API service, and GitHub Actions supplies the hourly schedule. No billable
Render database or cron resource is required. The current scope remains one
bounded, read-only PuntersEdge thoroughbred-results operation per run.

## LIVE-015 — Add freshness and coverage monitoring — COMPLETE

The hourly lane records fixed-detail success/failure events in the existing
append-only `source_health_events` table. Anonymous system status now exposes
only safe operational metadata: latest success and attempt timestamps,
provider response age, configurable freshness threshold, aggregate canonical
coverage, and a bounded failure code. The status view never returns provider
payloads, provider error text, credentials, or wagering fields. The Render
deployment and a fresh scheduled ingestion were verified against Neon.

## LIVE-016 — Add operator-facing live health status — IN PROGRESS

The licensed dashboard now consumes the safe `live_ingestion` status object and
renders explicit HEALTHY, STALE, FAILED, and NO DATA states with provider,
operation, last-success, freshness, and aggregate coverage metadata. It does
not render provider payloads, provider error text, credentials, forecasts,
markets, or a synthetic replacement. Local web typecheck, five web tests, and
the production build pass; hosted deployment verification is the remaining
acceptance step.

## LIVE-019 — Verify the hourly failure path — IN PROGRESS

The scheduler already uses `set -euo pipefail` and curl's
`--fail-with-body --silent --show-error`, so an ingestion `503` produces a
failed GitHub Actions run rather than a false success. The API contract test
also proves missing trigger configuration returns `503`, invalid trigger
credentials return `401`, and the health projection emits only the bounded
`INGESTION_FAILED` or `DATABASE_UNAVAILABLE` code. A workflow contract test
now guards these fail-closed properties; the ticket closes after the hosted
workflow and deployment evidence are recorded.

## Next ticket boundary

LIVE-017 is the authenticated hosted journey: complete the owner Auth0
handoff, prove protected live meeting/race/entry calls in the deployed UI, and
record that the session remains read-only with wagering disabled. The complete
epic/ticket sequence is in
`docs/deployment/RALPH_LIVE_E2E_EPICS.md`.
