# Ralph loop: live provider completion plan

Date: 2026-10-15

This is the execution plan for moving the private Nexus staging lane from
synthetic runtime data to bounded, read-only provider data. The lane remains
wagering-disabled throughout.

## Research conclusions

- Neon project `nexus-staging` is linked to the `production` branch.
- `DATABASE_URL` is the pooled application connection; `DATABASE_URL_UNPOOLED`
  is the direct migration connection.
- Render remains the API host. The free Render web service is retained; the
  database and scheduled job are not provisioned on Render.
- GitHub Actions is the scheduler. The workflow must exist on the repository's
  default `main` branch before its hourly schedule is active.
- Provider credentials and the Neon URLs stay in Render. GitHub receives only
  the ingestion URL and a separate trigger token.
- The live path is limited to `punters-edge`, `GET_RESULTS`,
  `THOROUGHBRED`, one bounded read per run, and read-only operation.

## Ticket sequence

| Ticket | Scope | Status | Depends on | Acceptance evidence |
|---|---|---|---|---|
| LIVE-005 | Neon project, env wiring, migrations, psycopg 3 compatibility | COMPLETE | — | Neon schema head `019_ingestion_jobs`; 38 public tables; API connects to Neon |
| LIVE-006 | Render secret and non-secret runtime configuration | COMPLETE | LIVE-005 | Render contains both Neon URLs, trigger token, provider key, licensed scope, and private approval fields; no secret is committed |
| LIVE-007 | GitHub Actions secret wiring and default-branch activation | COMPLETE | LIVE-006 | `NEXUS_INGESTION_URL` and trigger token are repository secrets; workflow exists on `main`; manual dispatch is available |
| LIVE-008 | Synthetic-runtime fail-closed control | COMPLETE | LIVE-005, LIVE-006 | Licensed mode cannot fall back to synthetic repositories; missing production configuration fails closed |
| LIVE-009 | Render deployment and post-deploy health verification | COMPLETE | LIVE-006, LIVE-007 | Latest deployment is live; migrations complete; `/health/live` is 200; system status is licensed/Postgres/read-only |
| LIVE-010 | First bounded provider ingestion and canonical persistence | COMPLETE | LIVE-007, LIVE-009 | Authenticated runs succeed; safe counters, receipts, envelopes, canonical rows, and post-fix idempotency are verified in Neon |
| LIVE-011 | Operational closeout | COMPLETE | LIVE-010 | Render serves licensed provider data only; failures are fail-closed; rollback/kill-switch procedure is documented and tested |
| LIVE-012 | Replace synthetic command cards with licensed canonical meetings | COMPLETE | LIVE-011 | Frontend reads `/v1/system/status` and `/v1/meetings`; licensed mode shows provider-backed cards and suppresses synthetic assistant claims |
| LIVE-013 | Expose canonical races by meeting | COMPLETE | LIVE-012 | Authenticated `/v1/meetings/{meeting_id}/races` returns bounded, as-of filtered licensed races; contract and Neon verification pass |
| LIVE-014 | Show licensed race and entry detail | COMPLETE | LIVE-013 | Frontend loads canonical races and entries, displays provenance/read-only state, and fails closed without synthetic replacement |
| LIVE-015 | Add freshness and coverage monitoring for the hourly lane | COMPLETE | LIVE-014 | Safe status reports latest success/attempt, provider response age, freshness threshold, aggregate canonical coverage, and bounded failure state; Render and Neon verification pass |
| LIVE-016 | Add operator-facing live health status | IN PROGRESS | LIVE-015 | Licensed dashboard shows bounded HEALTHY/STALE/FAILED/NO DATA state without payload leakage or synthetic replacement |
| LIVE-017 | Prove the authenticated hosted live journey | PLANNED | LIVE-016 | Auth0 owner session reaches live meeting, race, and entry views through protected API calls; wagering remains disabled |
| LIVE-018 | Capture repeatable live acceptance evidence | PLANNED | LIVE-017, LIVE-019 | Render, GitHub Actions, Neon, and authenticated UI evidence are recorded without secrets or raw provider payloads |
| LIVE-019 | Verify the hourly failure/alert path | IN PROGRESS | LIVE-015, LIVE-016 | Scheduled ingestion failure is non-zero/visible and status remains bounded |
| LIVE-020 | Run release go/no-go closeout | PLANNED | LIVE-018, LIVE-019 | Kill switch, rollback, no-synthetic, no-wagering, and scope boundaries are confirmed |

## Ralph loop protocol

For each ticket:

1. Research the current code, deployment state, and external dependency.
2. Design the smallest change and define observable acceptance checks.
3. Execute only that ticket's scoped change.
4. Run its checks and record the result here and in the ticket tracker.
5. Continue to the next ticket only when the acceptance criteria pass.

The loop stops for user action when a secret must be entered, a provider
account entitlement is ambiguous, or an external deployment state cannot be
changed safely. Secrets are never printed in logs or chat.

## Execution result

LIVE-005 completed locally and LIVE-006 through LIVE-011 completed in the staging lane:

- `neon init` linked the requested Neon project and `production` branch.
- `neon deploy` authenticated and pulled the three branch variables into the
  ignored `.env.local` file.
- Alembic applied all 19 revisions to Neon.
- The API now normalizes standard Neon URLs to the installed `psycopg` v3
  driver.
- `npm run build` passes.
- The API started against Neon and returned `LICENSED`, `postgres`,
  `punters-edge`, and `wagering_enabled=false`.
- The complete API suite passes: 334 tests.
- Render service `nexus-staging-api` is live on commit `cf4d59a`.
- GitHub workflow run `38717140368` succeeded with one bounded PuntersEdge
  `GET_RESULTS` read: one race, 12 entries, and one official result.
- A post-fix repeat run `38717707676` succeeded and returned zero new
  canonical results; Neon counts remained one meeting, one race revision, 12
  participants, 12 entries, and two official-result rows (one legacy row from
  the pre-idempotency deployment and one current canonical row).
- Neon latest rows are `punters-edge:GET_RESULTS` with `LICENSED` and
  `APPROVED` state. No provider payload or credential was printed.
- Render reports `HEALTH=ok`, `DATA_MODE=LICENSED`, `PERSISTENCE=postgres`,
  `PROVIDER=punters-edge`, `PROVIDER_ENABLED=True`,
  `PROVIDER_APPROVAL=APPROVED`, and `WAGERING_ENABLED=False`.
- The unauthenticated ingestion trigger returns `401`; the provider enable
  flag is the documented kill switch and missing enable/configuration fails
  closed in the runtime tests.
- LIVE-012 was merged as PR #179 and deployed to the static frontend; the
  deployed asset returns HTTP 200 and contains the licensed-mode meeting UI.
- LIVE-013 deployed in API commit `9bd2a48`; a Neon-backed scoped-auth check
  returned one `LICENSED` meeting and one matching `LICENSED` race, while the
  public Render route returned `401` without authentication.
- LIVE-014 was merged as PR #180 and deployed as frontend commit `db7ab11`;
  the asset contains the live race view, race-list and entry-list calls, and
  the explicit no-synthetic-replacement state.
- LIVE-015 was deployed as API commit `824dd6c`; Render deployment
  `dep-db8ark2vcj2c738rck2g` completed successfully and `/v1/system/status`
  returned a healthy licensed ingestion view after a fresh scheduled run.
- The new telemetry path recorded one `HEALTHY` event in Neon. The verified
  aggregate coverage is two licensed meetings, two races, 21 entries, and
  three official results; provider response age was 35 seconds at verification
  and the configured freshness threshold was 10,800 seconds.

## Post-closeout follow-up

The staging lane is operational and the first live data is visible through the
frontend. LIVE-015 is complete and LIVE-016 is the current Ralph ticket. The
full dependency-ordered release epics are in
`docs/deployment/RALPH_LIVE_E2E_EPICS.md`. Provider expansion or
historical/model use remains a separate decision requiring account entitlement
and retention evidence.
