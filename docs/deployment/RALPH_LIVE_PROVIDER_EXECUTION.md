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
| LIVE-006 | Render secret and non-secret runtime configuration | READY | LIVE-005 | Render contains both Neon URLs, trigger token, provider key, licensed scope, and private approval fields; no secret is committed |
| LIVE-007 | GitHub Actions secret wiring and default-branch activation | READY | LIVE-006 | `NEXUS_INGESTION_URL` and trigger token are repository secrets; workflow exists on `main`; manual dispatch is available |
| LIVE-008 | Synthetic-runtime fail-closed control | CODE COMPLETE / ACTIVATION PENDING | LIVE-005, LIVE-006 | Licensed mode cannot fall back to synthetic repositories; missing production configuration fails closed |
| LIVE-009 | Render deployment and post-deploy health verification | READY | LIVE-006, LIVE-007 | Latest deployment is live; migrations complete; `/health/live` is 200; system status is licensed/Postgres/read-only |
| LIVE-010 | First bounded provider ingestion and canonical persistence | READY | LIVE-007, LIVE-009 | One authenticated run succeeds; safe counters, receipt, envelope, canonical rows, and idempotency are verified in Neon |
| LIVE-011 | Operational closeout | READY | LIVE-010 | Render no longer serves synthetic data; failure is fail-closed; rollback/kill-switch procedure is documented and tested |

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

## Iteration 1 result

LIVE-005 completed locally:

- `neon init` linked the requested Neon project and `production` branch.
- `neon deploy` authenticated and pulled the three branch variables into the
  ignored `.env.local` file.
- Alembic applied all 19 revisions to Neon.
- The API now normalizes standard Neon URLs to the installed `psycopg` v3
  driver.
- `npm run build` passes.
- The API started against Neon and returned `LICENSED`, `postgres`,
  `punters-edge`, and `wagering_enabled=false`.
- The complete API suite passes: 332 tests.

## Next execution boundary

LIVE-006 is the next ticket. It requires entering the existing Neon connection
strings and a newly generated ingestion trigger token into the Render service.
Those values must be entered through the Render Dashboard or an authenticated
Render API session; they must not be committed or pasted into this document.
