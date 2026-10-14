# Live provider activation go-live plan

**Status:** PuntersEdge bounded diagnostic configuration is live in staging; the first owner-authenticated request is still pending

**Scope:** first controlled live-data activation for Nexus backend. Visual
owner review remains last. No wagering, trading, staking, order placement or
automatic external action is permitted.

## Current starting point

The Render service `nexus-staging-api` is live on the backend staging branch
in My Workspace. The service is healthy, runs on the Free plan in Singapore,
has automatic deploys disabled, and currently reports:

- provider credentials configured in Render;
- PuntersEdge enable and diagnostics flags enabled only for the bounded
  diagnostic path;
- the two non-secret PuntersEdge diagnostic approval records configured;
- FormFav, Krok Odds and Betfair Exchange remain disabled;
- `data_mode=SYNTHETIC_ONLY`;
- `external_connectivity=false` until the owner-authenticated diagnostic
  succeeds;
- no hosted PostgreSQL or queue/worker service.

The first activation target is PuntersEdge because Nexus already has a bounded
two-request diagnostic route for it. Do not enable all providers at once.

## Go-live gates

| Gate | Purpose | Required evidence | Go/no-go owner |
|---|---|---|---|
| G0 | Freeze and baseline | Current live deploy, clean error logs, passing backend suite, rollback deploy identified | Engineering |
| G1 | Rights and identity | Provider entitlement, Nexus-specific read/retention/display/model-use decision, owner subject and Auth0 `providers:read` permission | Owner + security |
| G2 | Bounded connectivity | Two-request PuntersEdge diagnostic succeeds; aggregate response only; no raw payload or secret leakage | Engineering |
| G3 | Durable data plane | Managed PostgreSQL, migrations, backups, restore test, worker/queue, retry/lease/alert evidence | Engineering + owner spend approval |
| G4 | Canonical live data | Provider response schema, identity/timestamp validation, scratchings/revisions/quarantine and provenance acceptance | Racing-domain owner |
| G5 | Model assurance | Approved historical sample, chronological walk-forward evaluation, leakage checks, calibration and abstention review | Data-science reviewer |
| G6 | Restricted pilot | Authenticated owner-only access, monitoring, rollback rehearsal and written go/no-go | Owner + independent reviewers |

No later gate may be marked complete from credentials alone.

## Phase 0 — freeze and preflight

1. Record the current Render deployment ID and commit.
2. Verify `/health/live`, `/v1/system/status`, OpenAPI and protected-route
   denial.
3. Confirm the provider API key is present without displaying or exporting it.
4. Confirm no credentials are present in Git, logs, browser bundles or approval
   documents.
5. Confirm Auth0 owner identity, issuer, audience, JWKS and the exact
   `providers:read` permission.
6. Confirm the selected provider and the exact operation/date/venue scope for
   the first diagnostic.

**Abort if:** the branch is not the intended backend branch, the service is
unhealthy, OIDC is not fail-closed, a secret appears in output, or the
provider scope is broader than the approved read-only operation.

## Phase 1 — configure the bounded diagnostic

For PuntersEdge, set the following in the Render API service. Values are
references and approvals only; never put API keys in these fields.

```text
NEXUS_PROVIDER_PUNTERS_EDGE_ENABLED=true
NEXUS_DIAGNOSTICS_ENABLED=true

NEXUS_PROVIDER_PUNTERS_EDGE_ACCOUNT_METADATA_APPROVAL_TIER=ACCOUNT_METADATA_READ
NEXUS_PROVIDER_PUNTERS_EDGE_ACCOUNT_METADATA_APPROVED_OPERATIONS=ACCOUNT_METADATA_READ
NEXUS_PROVIDER_PUNTERS_EDGE_ACCOUNT_METADATA_APPROVED_CODES=THOROUGHBRED
NEXUS_PROVIDER_PUNTERS_EDGE_ACCOUNT_METADATA_ACCOUNT_ENTITLEMENT_EVIDENCE=<owner reference>
NEXUS_PROVIDER_PUNTERS_EDGE_ACCOUNT_METADATA_CREDENTIAL_CUSTODIAN=owner
NEXUS_PROVIDER_PUNTERS_EDGE_ACCOUNT_METADATA_QUOTA_CEILING=<bounded request reference>
NEXUS_PROVIDER_PUNTERS_EDGE_ACCOUNT_METADATA_KILL_SWITCH_REFERENCE=<kill-switch reference>

NEXUS_PROVIDER_PUNTERS_EDGE_DIAGNOSTIC_APPROVAL_TIER=EPHEMERAL_READ_ONLY_DIAGNOSTIC
NEXUS_PROVIDER_PUNTERS_EDGE_DIAGNOSTIC_APPROVED_OPERATIONS=GET_RESULTS
NEXUS_PROVIDER_PUNTERS_EDGE_DIAGNOSTIC_APPROVED_CODES=THOROUGHBRED
NEXUS_PROVIDER_PUNTERS_EDGE_DIAGNOSTIC_ACCOUNT_ENTITLEMENT_EVIDENCE=<owner reference>
NEXUS_PROVIDER_PUNTERS_EDGE_DIAGNOSTIC_CREDENTIAL_CUSTODIAN=owner
NEXUS_PROVIDER_PUNTERS_EDGE_DIAGNOSTIC_QUOTA_CEILING=<bounded request reference>
NEXUS_PROVIDER_PUNTERS_EDGE_DIAGNOSTIC_KILL_SWITCH_REFERENCE=<kill-switch reference>
```

The existing `NEXUS_PROVIDER_PUNTERS_EDGE_API_KEY` remains a Render secret and
must not be copied into Git, chat, tickets or logs.

Save the variables and redeploy manually. Do not enable historical capture,
raw persistence, model training or display based only on this diagnostic
approval.

## Phase 2 — diagnostic acceptance

Use an owner-authenticated token containing `providers:read` to call:

```http
POST /v1/provider-probes/punters-edge
Content-Type: application/json

{"operation":"GET_RESULTS","code":"THOROUGHBRED","date":"YYYY-MM-DD","venue":"Randwick"}
```

Accept only if all conditions hold:

- the request is authenticated and scoped to `providers:read`;
- account metadata is the first request;
- the total request count is exactly two;
- the response contains only aggregate diagnostics;
- `raw_payload_retained` is `false`;
- no runner names, prices, credentials or raw provider errors appear in the
  response or logs;
- the deployment remains healthy and the error log remains empty;
- the kill switch can be set back to false and blocks a repeat request.

If any condition fails, immediately set both enable flags to false, redeploy,
and retain the failure correlation ID without retaining provider payloads.

## Phase 3 — durable live-data plane

Before any live capture is persisted or used by recommendations, provision and
approve:

1. Managed PostgreSQL with migrations and connection secret wiring.
2. A durable queue/worker topology with lease recovery, retry ceilings and
   graceful SIGTERM handling.
3. Backup, restore and migration rollback evidence.
4. Structured audit events and provider request/response correlation IDs.
5. Cost, quota and rate-limit alarms.
6. A retention policy matching the provider agreement.

This is a separate infrastructure change. The current Free Render service has
no database or worker; no production-like persistence should be simulated with
the ephemeral web-service filesystem.

## Phase 4 — first approved capture

After G1 and G3 are complete, create the full provider approval record for the
specific operation and code. Run one read-only capture with persistence off
first. Validate:

- provider and account identity;
- meeting, race and runner identifiers;
- scheduled, published, retrieved and effective timestamps;
- scratchings, reserves, coupled entries and field revisions;
- duplicate and replay behavior;
- quota and response-size limits;
- silks or other display metadata only where explicitly licensed.

Persist only the minimum approved envelope and provenance metadata. Quarantine
anything with missing identity, impossible timestamps, post-cutoff facts,
unapproved rights or schema drift.

## Phase 5 — recommendations gate

Do not label results as validated recommendations until the approved historical
sample has passed:

- chronological walk-forward evaluation;
- pre-cutoff/as-of leakage checks;
- B0–B4 baseline comparison;
- calibration, Brier/log-loss and coverage reporting;
- abstention and insufficient-data behavior;
- provider outage and stale-data tests;
- independent data-science review.

Until then, the API remains `SYNTHETIC_ONLY` or explicitly diagnostic-only.

## Rollback plan

Rollback is immediate and reversible:

1. Set `NEXUS_PROVIDER_PUNTERS_EDGE_ENABLED=false`.
2. Set `NEXUS_DIAGNOSTICS_ENABLED=false`.
3. Redeploy the last known-good commit.
4. Confirm `/health/live` is `ok`, status is synthetic-only and the provider
   route returns `503` or `401` as appropriate.
5. Review Render error/request logs and preserve only non-sensitive audit
   metadata.
6. Rotate the provider key if it appeared in any output or was exposed outside
   the secret store.

Automatic rollback is required for secret leakage, unexpected request count,
non-read-only behavior, raw payload retention, authentication bypass,
schema/identity failure, database write failure or unexplained provider quota
consumption.

## Final go-live decision

The first restricted pilot is **GO** only when G0–G5 are evidenced and the
owner signs G6. It is **NO-GO** while any provider approval, database/worker,
identity reconciliation, model assurance or independent review evidence is
missing.

The executable ticket mapping is maintained in
`docs/backlog/BACKEND_COMPLETION_8H.md` and
`docs/backlog/REMAINING_EPICS.md`.
