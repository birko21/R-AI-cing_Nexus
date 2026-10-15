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
| UX-003 | Validate responsive/accessibility behavior and deploy the reviewed UI | UX-001, UX-002 | IN PROGRESS |

## Safety boundary

This pass changes presentation and navigation only. It does not add market
data, forecasts, order/wager actions, new provider capabilities, or synthetic
fallback behavior in licensed mode.
