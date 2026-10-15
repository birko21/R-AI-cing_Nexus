# Frontend UI/UX and creative design review

Date: 2026-10-15  
Application: Racing Intelligence Lab / Nexus private staging  
Hosted URL: https://nexus-staging-frontend.onrender.com/  
Review type: visual, interaction, responsive, accessibility, trust-boundary, and release-readiness gate

## Executive verdict

**HOLD — not ready for creative sign-off as the agreed production experience.**

The application is working as an owner-only, read-only, provider-backed staging
slice. The live path is credible: Auth0 protects the page, the licensed API
reports current receipt health, meetings and canonical entries are visible, and
wagering, forecasts, and provider payloads are explicitly withheld.

However, the hosted product is not the full experience represented by the
agreed workspace-atlas design. The production path currently presents a
Command Centre, live meeting detail, and a capability boundary; most of the
14-workspace navigation entries resolve to bounded `NOT_AVAILABLE` panels.
That is a valid staged capability boundary, but it is not a completed creative
or product-design implementation. The user's observation that the agreed UI
has not appeared in production is therefore correct.

## Evidence reviewed

- Hosted page observed in Chrome on 2026-10-15. Public access correctly stops
  at `Nexus owner sign-in required`.
- Authenticated hosted acceptance recorded in
  `docs/deployment/RALPH_FRONTEND_UX_EXECUTION.md`: licensed mode, live
  ingestion monitor, two meeting cards, Northam Race 8, 12 entries, 9 active,
  3 scratched, receipt verification, and sign-out owner gate.
- Automated release packet in
  `docs/evidence/live-release/LIVE_RELEASE_EVIDENCE.md`: API-to-Neon-to-Auth0
  read-only journey, `WAGERING_ENABLED: False`, protected meetings returning
  `401`, and frontend returning `200`.
- Agreed visual references:
  - `docs/evidence/ril-018/workspace-atlas-desktop.png` — 1440x900
  - `docs/evidence/ril-018/workspace-atlas-tablet.png` — 768x1024
  - `docs/evidence/ril-018/workspace-atlas-mobile.png` — 390x844
  - `docs/evidence/ril-018/workspace-atlas.md`
- Implementation and test evidence in `apps/web/src/App.tsx`,
  `apps/web/src/styles.css`, and `e2e/command-centre.spec.ts`.

## Review scorecard

| Area | Verdict | Evidence and interpretation |
|---|---|---|
| Authentication and privacy | **PASS** | Hosted page is owner-gated; prior hosted pass returned to the owner sign-in screen after sign-out and public meetings access was `401`. |
| Live-data truthfulness | **PASS with P1 issue** | Licensed cards and race detail carry read-only, licensed, receipt, and no-wagering language. The initial client state still starts as `SYNTHETIC_ONLY` while the API is being checked, which can expose a synthetic first paint before mode resolution. |
| Provenance and capability boundary | **PASS** | Receipt verification, field counts, active/scratched state, and explicit unavailable forecasts/markets/wagering are strong and aligned with the no-wagering ADR. |
| Core live interaction | **PASS for staging scope** | Meeting cards open the canonical meeting/race/entry view; the detail view has a clear hierarchy and styled state chips. |
| Information architecture | **HOLD** | The nav exposes 14 workspaces as clickable peers, but most currently resolve to bounded placeholder panels. The information architecture promises more depth than production delivers. |
| Creative identity | **HOLD** | The dark analytical palette and badges are coherent, but the hosted surface is still a generic dashboard shell. The agreed creative language—distinctive racing identity, runner/tactical visual system, richer workspace composition, and clear product brand expression—is not present as a complete system. |
| Responsive behavior | **PASS for the tested shell; HOLD for product completeness** | Desktop/tablet/mobile screenshots and CSS breakpoints exist. Mobile relies on horizontal workspace-nav and horizontal table overflow; this needs human device review and clearer affordance before sign-off. |
| Accessibility | **PASS for automated baseline; HOLD for independent assurance** | The browser suite includes axe and keyboard-focus assertions. This is not a substitute for a real-device, screen-reader, zoom, contrast, and touch review. |
| Loading, empty, and error states | **HOLD** | Explicit states exist, but the licensed boot path has no isolated loading mode: it begins in synthetic mode and changes after API hydration. This is a trust and experience defect, not merely a cosmetic issue. |
| Production readiness | **HOLD** | The live read-only staging lane is testable. The agreed full UI/UX and creative release is not yet present in production. |

## What is working well

1. The visual foundation is consistent: deep navy surfaces, blue analytical
   accents, gold warnings, green positive states, compact uppercase metadata,
   and rounded evidence panels.
2. The live view avoids the most dangerous ambiguity. It says `LIVE READ-ONLY`,
   `LICENSED`, and `WAGERING DISABLED`, and does not display forecasts,
   bookmaker markets, or raw provider payloads.
3. The meeting-to-race-to-entry interaction is understandable. Counts for
   total, active, and scratched entries give the user a useful first read.
4. Provenance is treated as part of the interface rather than hidden in a
   debug view: receipt ID, provider lane, operation, freshness, and field
   revision are visible or explicitly bounded.
5. The shell has responsive evidence and a machine-tested focus/axe baseline.

## Release-blocking findings

### P0 — The production surface is a partial atlas, not the agreed complete experience

The agreed design reference shows a composed workspace atlas with real
workspace-level context, provenance, and evidence treatment. In the hosted
application, the navigation still presents Meeting discovery, Tactical track,
Runner intelligence, Models, Scenarios, Markets, Evidence, Assistant, Notebook,
Watchlists, and Reports/settings as peers, while the implementation routes most
of them to a generic bounded panel. This is honest about capability, but the
visual and interaction promise is misleading.

Decision required: either build the agreed workspace depth, or change the
navigation to a deliberately staged information architecture (for example,
`Live now`, `Research preview`, and `Not enabled`) so the production surface
does not imply completed features.

### P1 — Licensed boot can show synthetic content before API mode resolves

`apps/web/src/App.tsx` initializes `dataMode` to `SYNTHETIC_ONLY` and then
switches to `LICENSED` after the status request returns. In a hosted owner
session, the first paint can therefore show `DEMO ONLY`, synthetic cards, and
the synthetic assistant while the header is still checking the API. That is
contrary to the trust promise of a licensed live-data experience and creates an
avoidable risk of users reading synthetic content as current data.

The fix is a first-class `LOADING` or `UNKNOWN` mode that renders a neutral
licensed-session skeleton until the API mode is known. Synthetic content must
not mount during that interval.

### P1 — Creative system is not yet complete

The current palette and component styling are a good analytical baseline, but
they do not yet amount to the agreed creative direction. There is no complete
brand mark or distinctive racing visual language in the hosted flow, no
production Tactical Track/runner treatment, and no reference-by-reference
creative comparison proving that the experience is visually faithful rather
than merely structurally similar.

### P1 — Mobile navigation and data tables need an intentional interaction model

The responsive shell prevents a hard layout collapse, but its primary workspace
navigation is a long horizontal strip and the live entry table becomes a
horizontal overflow region on narrow screens. These patterns can be valid, but
they need visible scroll affordance, preserved active-item context, touch-size
verification, and a human device pass. The current automated evidence does not
prove that the mobile experience feels deliberate.

## Prioritized next tickets

| Ticket | Priority | Outcome | Acceptance evidence |
|---|---:|---|---|
| UX-REVIEW-001 | P0 | Replace synthetic-first boot with an explicit `LOADING`/`UNKNOWN` mode. No synthetic labels, assistant, cards, or filters render until mode resolution. | Playwright test asserts no `DEMO ONLY`, `SYNTHETIC_ONLY`, synthetic URI, or synthetic card during API checking; licensed and API-failure screenshots captured. |
| UX-REVIEW-002 | P0 | Resolve the workspace promise. Build the agreed workspace slices in dependency order, or redesign navigation into clear Live / Preview / Disabled groups. | 14-entry matrix updated; every visible nav item has a meaningful destination and state; desktop/tablet/mobile captures show no misleading peer-level placeholders. |
| UX-REVIEW-003 | P1 | Establish the creative foundation: product mark, typography scale, iconography, state language, racing/tactical visual vocabulary, and approved component tokens. | Reference-by-reference visual comparison against the approved atlas, with owner variance notes and rights ledger for every new asset. |
| UX-REVIEW-004 | P1 | Make mobile navigation and live entry data intentional. Add scroll affordance or compact navigation, responsive table treatment, and touch/zoom review. | 390x844 and real iOS/Android captures, keyboard/focus review, no clipped primary action, and readable entry state at 200% zoom. |
| UX-REVIEW-005 | P1 | Add a real loading/error/stale/denied visual state system for licensed mode. | State matrix, visual captures, and tests for healthy, stale, no-data, provider-failed, Auth0 denied, and API timeout paths. |
| UX-REVIEW-006 | P2 | Complete independent accessibility and creative-owner review. | WCAG 2.2 AA review notes, screen-reader/keyboard/touch results, named creative-owner decision, and explicit variance register. |
| UX-REVIEW-007 | P2 | Refresh the hosted release evidence after the design gate. | Current Render commit/deploy ID, authenticated browser captures, API verification output, and release decision all point to the same immutable build. |

## Recommended execution order

1. Complete UX-REVIEW-001 immediately because it protects the truth boundary.
2. Decide UX-REVIEW-002 before investing further in polish; the product cannot
   be judged as complete while the navigation contract is unresolved.
3. Execute UX-REVIEW-003 and UX-REVIEW-004 together as the creative/responsive
   implementation pass.
4. Run UX-REVIEW-005 and UX-REVIEW-006 as the independent assurance pass.
5. Re-run UX-REVIEW-007 and make the final creative release decision.

## Final decision

**Functional licensed staging:** GO for private owner testing of the
read-only provider path.

**Agreed UI/UX and creative experience:** NO-GO / HOLD. The application needs
the boot trust fix, a resolved workspace IA, completed creative system, and
human responsive/accessibility/creative-owner review before it can be described
as the agreed production design.

No application code or deployment was changed during this review.
