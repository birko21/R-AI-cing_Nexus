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

## LIVE-005 — Wire Render PostgreSQL and migrations — CODE COMPLETE / RESOURCE PENDING

The Alembic chain and transactional live-ingestion runner are ready. The
Render Blueprint declares the managed PostgreSQL resource and migration hook,
but the resource has not been created.

## LIVE-006 — Add scheduled ingestion — CODE COMPLETE / CRON PENDING

`scripts/run_live_provider_ingestion.py` is ready for a Render Cron service.
Each run performs one bounded read, persists the approved receipt/envelope,
projects canonical data, and exits without placing orders or wagers.

## LIVE-007 — Remove synthetic runtime fallback — CODE COMPLETE / ACTIVATION PENDING

Synthetic repositories remain available only for local/test mode. A licensed
deployment fails closed unless PostgreSQL and the explicit live scope are
configured. The current Render service remains synthetic until LIVE-005 and
LIVE-006 are applied.

## LIVE-008 — Deploy and validate on Render — IN PROGRESS

Commit `4209bf1` is live and health-checked. Final validation requires the
managed database, cron service, non-secret live scope configuration, one
bounded provider sample, and verification of persisted canonical rows.

## Current external gate

Render is currently on the Hobby plan with no payment method configured.
Creating the managed PostgreSQL and Cron resources may require a plan or
billing change. No billable resource has been created by this migration.
