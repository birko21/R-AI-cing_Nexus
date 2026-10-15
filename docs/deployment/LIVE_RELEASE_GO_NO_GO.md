# Live release go/no-go

Date: 2026-10-15

## Decision

**GO for the private owner-only, read-only staging journey.**

**NO-GO for public customer access, forecasts, markets, wagering, payouts,
Betfair liquidity, provider expansion, or production release.**

The approved scope is one bounded licensed `punters-edge` `GET_RESULTS` read
per scheduled run, persisted in Neon/Postgres and exposed through the
authenticated hosted UI without raw provider data.

## Acceptance gates

| Gate | Result | Evidence |
|---|---|---|
| Live release evidence is repeatable and secret-free | PASS | `scripts/verify_live_release.ps1` returned `RESULT: PASS`; packet in `docs/evidence/live-release/LIVE_RELEASE_EVIDENCE.md` |
| Provider and persistence are live | PASS | `LICENSED`, `postgres`, `punters-edge`, `GET_RESULTS`, `HEALTHY`; 2 meetings, 2 races, 21 entries, 3 results |
| Authenticated browser journey works | PASS | Auth0 owner sign-in reached the live dashboard, Northam Race 8, and 12 canonical entries (9 active, 3 scratched) |
| Unauthenticated access remains closed | PASS | Sign-out returned the owner gate; public `GET /v1/meetings` returned `401` |
| Synthetic fallback is excluded from licensed runtime | PASS | Licensed runtime selects Postgres; explicit provider activation is required; focused runtime and full API tests pass |
| Wagering and sensitive provider data remain excluded | PASS | `wagering_enabled=false`; UI is read-only and omits payloads, forecasts, markets, and wagering controls; safe status has no `payload` field |
| Failure path is fail-closed | PASS | Missing/invalid trigger configuration returns bounded `503`/`401`; scheduler uses failing curl semantics; LIVE-019 contract test and hosted workflow passed |
| Kill switch is defined and testable | PASS | The provider enable flag is the kill switch; missing enablement raises `ProviderActivationError` and the runner does not ingest |
| Rollback target is identified | PASS | Revert the staging service to the previous successful Render deploy in service history; for the frontend, the immediately previous known-good deploy is `dep-db8ajtgu01pc73f4khcg` from `db7ab11` |

## Operational notes

- No live kill-switch toggle was performed during closeout because doing so
  would intentionally interrupt the currently verified staging lane. The
  fail-closed behavior is covered by the runtime contract tests and is
  reversible through Render's environment/deploy history.
- The release evidence deliberately records aggregate counts and bounded
  labels only. Credentials, tokens, browser storage, provider payloads, and
  provider error text are not part of the packet.
- The next change requiring a new release decision is any expansion beyond
  the bounded results operation or the private owner-only staging audience.

## Ticket closure

- LIVE-018 — COMPLETE: repeatable evidence packet captured.
- LIVE-020 — COMPLETE: go/no-go decision recorded and all release gates pass
  for the explicitly limited staging scope.
