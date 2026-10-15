# Ralph frontend UI/UX execution

Date: 2026-10-15

## Agreed experience used for this pass

The implementation target is the existing design-rescue evidence, not a new
visual direction:

- `docs/evidence/ril-018/workspace-atlas-desktop.png`
- `docs/evidence/ril-018/workspace-atlas-tablet.png`
- `docs/evidence/ril-018/workspace-atlas-mobile.png`
- `docs/evidence/ril-018/workspace-atlas.md`
- `docs/PROJECT_SPRINT_PLAN.md` tickets NXD-012 through NXD-019
- `docs/adr/0003-no-wagering-and-data-modes.md`

The live extension preserves the same dark analytical shell, shared workspace
navigation, explicit provenance/state language, responsive behavior, and
read-only boundary. Licensed mode must not expose synthetic availability
examples or imply forecasts, markets, or wagering.

## Discovery findings

The hosted browser audit found:

1. The current live page had no workspace-atlas navigation.
2. Licensed mode still showed synthetic-only state filters and “Show
   availability examples”.
3. Live cards used “Fixture time” and said race detail was coming in a future
   ticket even though live race detail was already deployed.
4. The authenticated toolbar displayed the owner email unnecessarily.
5. Live entry states were raw table text rather than the designed state chips.
6. The live meeting view needed a stronger hierarchy for counts, field state,
   provenance, and the unavailable capability boundary.

## Ticket sequence

| Ticket | Outcome | Depends on | Status |
|---|---|---|---|
| UX-001 | Restore the shared workspace shell and make licensed/synthetic controls and copy truthful | Discovery | COMPLETE |
| UX-002 | Improve live meeting/race detail hierarchy, state chips, provenance, and degraded states | UX-001 | COMPLETE |
| UX-003 | Validate responsive/accessibility behavior and deploy the reviewed UI | UX-001, UX-002 | COMPLETE |

## UX-003 validation notes

The default Playwright run initially reused a Vite server from a different
workspace. The test harness now accepts `WEB_PORT` and
`PLAYWRIGHT_REUSE_SERVER=false` so a fresh branch-local server can be forced.
The isolated rerun passed all six existing browser journeys, including axe,
desktop/mobile screenshots, and the workspace navigation regression.

Observed commands:

```text
npm run typecheck                         PASS
npm run test -- --run                     5 passed
npm run build                             PASS
$env:WEB_PORT='5174'; $env:PLAYWRIGHT_REUSE_SERVER='false'; pnpm web:e2e
                                            6 passed (31.5s)
```

Evidence captures were refreshed at `docs/evidence/ril-017` through
`docs/evidence/ril-061`. The browser suite includes the 390px mobile viewport
and an axe scan; the hosted licensed browser pass remains the final live-data
acceptance check after deployment.

## Hosted acceptance

- Render service `nexus-staging-frontend` deployed commit `69e15f2` as
  `dep-db8bi60u01pc73f7k7h0`; Render reports `status: live` and a successful
  Vite build.
- Auth0 owner session reached licensed mode after API hydration and showed the
  workspace atlas, live ingestion monitor, two meeting cards, and the licensed
  capability boundary.
- Northam opened to Race 8 with 12 total entries, 9 active, 3 scratched,
  styled state chips, a verified receipt, and no provider payloads or
  forecasts displayed.
- Sign-out returned to `Nexus owner sign-in required`.

## Ralph closeout

UX-001, UX-002, and UX-003 are complete for the approved private,
owner-only, read-only licensed staging experience. Further workspaces remain
explicitly bounded until their data and rights gates are approved; no wagering
or synthetic fallback was added.

## Safety boundary

This pass changes presentation and navigation only. It does not add market
data, forecasts, order/wager actions, new provider capabilities, or synthetic
fallback behavior in licensed mode.
