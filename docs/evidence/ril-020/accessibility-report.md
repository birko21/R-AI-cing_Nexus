# RIL-020 accessibility and degraded-state report

## Scope

The synthetic command centre exposes loading, stale snapshot, no racing, no data, quarantined, unsupported, unavailable and auth-denied states. Each state is labelled in the card status and has a plain-language explanation; no partial, inferred or live values are displayed.

## Automated evidence

Command: `pnpm web:e2e`

Result: `3 passed`

- Axe scan: zero violations on the default command-centre fixture, including colour-contrast checks.
- Keyboard: code filter receives focus and exposes `aria-pressed` state.
- Screen reader structure: labelled command-card region, labelled filters, named tabs, table captions and status text.
- Responsive evidence: `degraded-desktop.png` and `degraded-mobile.png`.

## Interaction controls

- Interactive controls use a minimum 44px height and visible focus outlines.
- The data-state selector exposes every degraded state as a labelled option.
- The empty/no-data path explains that no values are inferred.
- Auth-denied, unsupported and quarantined states explain the blocking condition rather than rendering a fabricated result.

