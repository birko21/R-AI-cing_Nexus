# Ralph Loop: V7 Visual Implementation Review

Date: 2026-10-16  
Scope: local visual implementation in `apps/web`  
Reference: `NEXUS_CODEX_VISUALS_ESSENTIALS.zip`

## Outcome

The local implementation now provides a complete visual pass across the 14 approved workspaces and the required 1440x900, 768x1024, and 390x844 responsive states. It follows the approved V7 direction and preserves the evidence-first product boundary:

- midnight navy racing environment with mineral/slate analytical surfaces;
- champagne/gold accents for active, caution and quality-gate states;
- cinematic track imagery and layered synthetic runner assets;
- unique workspace surfaces rather than generic empty previews;
- explicit synthetic, illustrative and rights-pending labels;
- responsive workspace navigation and readable mobile layouts;
- no wagering, forecast or live-data claims are inferred from the visual layer.

## Discovery and design decisions

The attached pack was reviewed as the visual source of truth. The implementation was checked against the canonical boards and the 14 screen references, with the following non-negotiables carried into code:

1. The Command Centre is a cinematic daybook with a hero race surface, metrics, insight stack, filters, evidence assistant and state-labelled research cards.
2. Tactical Track is a side-on visual race-reading surface with an inside rail, grouped 2–3-abreast runner layers, independently placeable runners, scenario switching, selected-runner detail and a linked speed map.
   The field layout is now data-sized: the renderer recalculates group allocation and runner coordinates for the current field rather than assuming 11 runners. The synthetic QA control exercises 6, 8, 11, 14 and 20-runner states; the provider-entry collection can replace this synthetic collection in the live wiring pass.
3. The remaining workspaces have distinct hero/readout/analysis treatments appropriate to their purpose: meeting discovery, race context, runner intelligence, comparison, models, scenarios, markets, evidence, assistant, notebook, watchlists and reports/assurance.
4. Settings and Assurance are designed as an owner-control surface with provenance, access, rights and export boundaries visible rather than hidden.
5. Mobile uses the same information hierarchy and visual language without relying on tiny type or removing the evidence state.

## Execution evidence

Screenshots are stored in `docs/evidence/v7-implementation/`:

- `command-centre-1440.png`, `command-centre-768.png`, `command-centre-390.png`
- one 1440, 768 and 390 capture for each of Meetings, Race, Tactical, Runner, Compare, Models, Scenarios, Markets, Evidence, Assistant, Notebook, Watchlists and Reports.
- `tactical-6-1440.png` and `tactical-14-1440.png` prove that the track, grouped field, detail state and speed map adapt to different runner counts.

The focused Playwright coverage is `e2e/v7-visual.spec.ts`. It verifies all 14 workspace routes, synthetic-state labelling, responsive captures, the 11-runner tactical field, base/contested scenario switching and runner selection.

## Production boundary

This pass is intentionally local. No Render, Auth0 or provider configuration was changed. The track backdrop and runner layers are feasibility assets copied from the existing synthetic design-rescue material; they remain rights-pending and are labelled in the UI. The visual implementation can therefore be reviewed and tested locally, but production asset approval and the independent visual-owner gate remain separate release conditions.

## Ralph exit criteria

The local visual implementation exit criteria are met only when all of the following remain true after the final verification run:

- typecheck, production build and unit tests pass;
- the full existing browser suite passes;
- the V7 visual suite passes at all three responsive sizes;
- no whitespace errors are reported by `git diff --check`;
- the captures visibly retain the approved atmosphere, information density, evidence labelling and responsive hierarchy.
