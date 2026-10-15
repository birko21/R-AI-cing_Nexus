# Phase 0 next-workspace handoff

**Current gate:** Tactical Track visual candidate ready for human review; production HOLD remains.

## What is complete before handoff

- Metadata-driven Tactical Track fixture contract is defined in `TACTICAL_TRACK_METADATA_CONTRACT.md`.
- Synthetic Betfair-shaped fixture is available at `apps/web/public/tactical-track-fixture.js`.
- The lab renders from per-runner `silks` metadata and works from both HTTP and direct `file://` opening.
- Asset state and production replacement requirements are recorded in `TACTICAL_TRACK_ASSET_STATUS.md`.
- Human review packet is ready in `TACTICAL_TRACK_REVIEW_PACKET.md`.

## Gate before advancing

Do not start the next workspace until the review packet contains both an independent reviewer decision and an owner decision. If either decision is `REVISE` or `HOLD`, return to Tactical Track and preserve the production hold.

## Next dependency-ordered work

1. **NXD-010 — Create matched Tactical View and analytical pace-map mobile UX** (#159). This is the immediate remaining Tactical Track/mobile evidence item; it depends on the spatial grouping contract and must use the same selected runner, scenario, silk, and caveats in both modes.
2. **NXD-011 — Validate code-specific thoroughbred, harness and greyhound mechanics** (#160). This is the next distinct workspace-level domain review after NXD-010, and it requires named independent specialists. No expert approval is inferred.
3. **NXD-012 — Establish premium Dual Atmosphere components and identity tokens** (#161). Begin only after the Tactical Track gate and the preceding dependencies are resolved.

Each next increment must retain the V7 evidence contract: real 1440×900, 768×1024, and 390×844 browser captures, protected-reference comparison, rights/design-state declaration, automated checks, and recorded human decisions.
