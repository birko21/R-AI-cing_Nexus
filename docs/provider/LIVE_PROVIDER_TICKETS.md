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

## LIVE-005 — Wire PostgreSQL and migrations — COMPLETE LOCALLY / RENDER PENDING

The Alembic chain and transactional live-ingestion runner are ready. The
`nexus-staging` Neon project and `production` branch are now linked. The
pooled and direct URLs are available through the ignored local `.env.local`,
all 19 migrations have been applied, and the API uses the installed psycopg 3
driver. The free Blueprint still expects the same URLs as Render secrets;
Render does not create a paid database resource.

## LIVE-006 — Wire Render runtime secrets — READY / RENDER ACTION PENDING

Enter the pooled and direct Neon URLs, the existing PuntersEdge API key, a
new ingestion trigger token, and the non-secret licensed read-only scope into
`nexus-staging-api`. Keep provider credentials and database URLs in Render.

## LIVE-007 — Add scheduled ingestion — CODE COMPLETE / GITHUB SECRETS PENDING

The protected `/internal/live-ingestion/run` endpoint performs one bounded
read using provider credentials held in Render. A GitHub Actions schedule
triggers it hourly, avoiding Render's paid Cron service. Each run persists the
approved receipt/envelope, projects canonical data, and exits without placing
orders or wagers.

## LIVE-008 — Remove synthetic runtime fallback — CODE COMPLETE / ACTIVATION PENDING

Synthetic repositories remain available only for local/test mode. A licensed
deployment fails closed unless PostgreSQL and the explicit live scope are
configured. The current Render service remains synthetic until the Neon,
Render, GitHub, and deployment tickets are applied.

## LIVE-009 — Deploy and validate on Render — READY / CONFIGURATION PENDING

The existing free API service is live and health-checked. Final validation
requires the Neon secrets, GitHub workflow, non-secret live scope
configuration, one bounded provider sample, and verification of persisted
canonical rows.

## LIVE-010 — Verify canonical persistence and idempotency — READY / FIRST RUN PENDING

Confirm that one successful provider run creates the expected receipt,
envelope, and canonical rows in Neon, then repeat the same run to prove that
the idempotency boundary does not duplicate data.

## LIVE-011 — Operational closeout — READY / VALIDATION PENDING

Record the safe response shape, failure behavior, kill-switch procedure, and
rollback steps. Confirm that provider failures fail closed and that the API
never exposes raw payloads, credentials, or wagering operations.

## Current external gate

The free path requires a Neon pooled URL, Neon direct URL, and one matching
ingestion trigger token entered as secrets in Render/GitHub. No billable
Render resource is required. Scheduled workflows run from the repository's
default branch, so the workflow must be merged there before hourly execution.

The full dependency-ordered Ralph sequence and completed evidence are recorded
in `docs/deployment/RALPH_LIVE_PROVIDER_EXECUTION.md`.
