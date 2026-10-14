# Workspace atlas engineering evidence

## Scope

The authenticated synthetic web shell now exposes fourteen keyboard-accessible
workspace entries: Command Centre, Meeting discovery, Race intelligence,
Tactical track, Runner intelligence, Runner comparison, Model laboratory,
Scenario studio, Markets, Evidence, Research assistant, Notebook, Watchlists
and alerts, and Reports/settings.

Every workspace preserves the same code, race, field revision and model-state
context. The views are synthetic-only and explicitly label unavailable,
restricted, illustrative and non-promoting states.

## Automated evidence

Command: `$env:VITE_AUTH_REQUIRED='true'; pnpm web:e2e`

The workspace-atlas test checks all fourteen navigation entries, shared
context, tactical/model/evidence transitions, mobile axe scanning and these
browser captures:

- `workspace-atlas-desktop.png` — 1440×900
- `workspace-atlas-tablet.png` — 768×1024
- `workspace-atlas-mobile.png` — 390×844

This is implementation evidence only. The required visual-owner,
accessibility-reviewer, racing-domain/model-trust and rights decisions remain
open gates.
