# UAT readiness Ralph Loop — 2026-10-16

## Decision

**READY FOR OWNER UAT — private, authenticated, read-only staging scope.**

This is not approval for public access, wagering, forecasts, markets, provider
expansion, or a production customer release.

## Discovery findings

| Finding | Result |
|---|---|
| Render frontend source | Tracked `codex/live-provider-staging`; the hosted service was behind the validated V7 candidate |
| Hosted API | Healthy licensed lane; PuntersEdge `GET_RESULTS`; Neon/Postgres persistence; wagering disabled |
| Auth boundary | Auth0 owner session active in the hosted browser; anonymous `GET /v1/meetings` returns `401` |
| Hosted UI taxonomy | V7 candidate contains the 14-screen atlas plus an explicit owner-only Analysis Lab mode |
| Provider journey | Live dashboard and canonical meeting/race/entry flow are available without synthetic fallback |

## Executed tickets

| Ticket | Outcome | Evidence |
|---|---|---|
| UAT-001 | Pushed V7 candidate to the Render-tracked branch | Commit `f0059f2`; branch push completed |
| UAT-002 | Deployed the frontend only | Render deploy `dep-db8k4fqrl0oc738vh9ug` is `live` |
| UAT-003 | Verified hosted owner dashboard | `LICENSED`, `API READY`, `HEALTHY`; 3 meetings, 3 races, 31 entries, 4 results |
| UAT-004 | Verified live meeting detail | Northam → Race 8; 12 entries, 9 active, 3 scratched; receipt verified |
| UAT-005 | Verified safety boundary | UI states `LIVE READ-ONLY`, `LICENSED`, `DISABLED`; provider payloads and forecasts are not displayed |
| UAT-006 | Verified public denial | `GET /v1/meetings` without a bearer token returned `401 Unauthorized` |
| UAT-007 | Re-ran repository checks | 338 API tests passed; contract validation passed; Render blueprint validation passed; web checks/build/E2E already passed on the deployed commit |
| UAT-008 | Created this handoff record | No tokens, credentials, raw provider payloads, or browser storage captured |
| UAT-009 | Added owner-only Analysis Lab switch | Full V7 visual journey is available as deterministic synthetic fixtures; Live Evidence remains provider-backed and bounded |

## Owner UAT sequence

1. Open <https://nexus-staging-frontend.onrender.com/>.
2. Sign in with Auth0 as the allowlisted owner.
3. Confirm `LICENSED INGESTION MONITOR` and a bounded `HEALTHY`, `STALE`, `FAILED`, or `NO DATA` state.
4. Open a live meeting and confirm the `LIVE RESEARCH VIEW · READ-ONLY`, a licensed race panel, canonical entries, field states, and receipt.
5. Confirm no forecasts, market odds, wagering actions, raw provider payloads, or synthetic replacement values appear in the licensed journey.
6. Choose `Analysis lab`, confirm the `OWNER ANALYSIS LAB` banner, and exercise the complete atlas at desktop, tablet, and mobile sizes; compare against the canonical pack and record visual approval or defects.
7. Switch back to `Live evidence` and confirm the licensed dashboard and canonical meeting flow return.
8. Sign out and reload; confirm the owner gate returns.

## Remaining gates

- Owner visual approval against the canonical V7 pack is still required.
- Owner must confirm the hosted live-data journey is acceptable for UAT.
- Provider rights/retention scope remains limited to the approved private read-only lane.
- Keep the kill switch, rollback target, and no-wagering boundary unchanged during UAT.
