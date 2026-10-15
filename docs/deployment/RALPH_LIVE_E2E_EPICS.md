# Ralph loop: live end-to-end release epics

Date: 2026-10-15

This is the dependency-ordered release register for taking the private Nexus
staging lane through a real hosted, authenticated, read-only live-data test.
The scope is deliberately bounded to the existing licensed lane:
PuntersEdge `GET_RESULTS`, Thoroughbred data, Neon persistence, Render API,
GitHub Actions scheduling, Auth0 owner access, and wagering disabled.

## Epics and tickets

| Epic | Ticket | Outcome | Depends on | Ralph acceptance gate |
|---|---|---|---|---|
| E1 · Live operations | LIVE-016 | Show safe ingestion health in the licensed dashboard | LIVE-015 | Deployed UI visibly distinguishes HEALTHY, STALE, FAILED, and NO DATA; no provider payload or synthetic replacement is rendered |
| E1 · Live operations | LIVE-019 | Preserve an actionable failure path for the hourly lane | LIVE-015, LIVE-016 | A 503 from the protected ingestion route fails the scheduled job, while the status surface exposes only a bounded failure code |
| E2 · Authenticated hosted journey | LIVE-017 | Prove the Auth0 owner session reaches live meetings, races, and entries | LIVE-016 | Owner sign-in succeeds; protected API calls return live licensed records; unauthenticated access remains denied; wagering remains disabled |
| E3 · Release evidence | LIVE-018 | Produce a repeatable live acceptance record | LIVE-017, LIVE-019 | Evidence records Render deploy, successful provider run, Neon health/coverage counts, and the authenticated UI path without secrets or raw payloads |
| E4 · Go/no-go closeout | LIVE-020 | Confirm the lane is safe to keep running | LIVE-018 | Runbook confirms kill switch, rollback target, no synthetic fallback, no wagering path, and explicit out-of-scope capabilities |

## Explicitly out of this release gate

Provider expansion, historical/model training, forecasts, market odds,
Betfair liquidity, wagering, and production customer access are not required to
prove this first real live end-to-end path. They remain separate epics that
need their own provider entitlements, retention decisions, and acceptance
criteria.

## Execution order

Ralph completes one ticket at a time. Each ticket must have a code or
deployment change, observable acceptance checks, and an evidence entry before
the next ticket starts. Auth0 credentials are entered only by the owner in the
browser; they are never copied into the repository, terminal output, or ticket
evidence.
