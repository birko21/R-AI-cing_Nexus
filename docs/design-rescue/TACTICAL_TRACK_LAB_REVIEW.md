# Tactical Track Feasibility Lab Review

**Status:** VISUAL CANDIDATE ADVANCED · PRODUCTION HOLD
**Scope:** Tactical Track only; no approval for the remaining 13 workspaces.
**Draft PR:** https://github.com/birko21/R-AI-cing_Nexus/pull/177
**Lab URL:** `http://127.0.0.1:5173/tactical-track-lab.html`

## Candidate delivered

The lab is a standalone public HTML entry, not a production route. It uses one synthetic fixture with eleven independently positioned transparent horse-and-jockey image layers over a runner-free generated turf backdrop. The same fixture supports:

- Base case and Contested lead scenarios;
- visible inside rail, start/finish axis, 0–400 m early-settling framing, and two- to three-abreast groups;
- selected-runner detail, evidence caveat, and linked analytical pace-map treatment;
- responsive desktop, tablet, and mobile layouts;
- explicit synthetic/illustrative and rights-pending labels.

The runner field was iterated after the first review: the geometric SVG treatment was removed, photorealistic synthetic horse-and-jockey layers were added, and dense name pills were reduced to a selected-runner label plus numbered identity markers. Full runner names remain in the linked groups and detail panel so the track remains readable at mobile width.

The backdrop was then iterated again from a bend to a straightaway. Parallel rails now sit behind the field, leaving the compositing zone open so runners do not visually intersect the fence.

The backdrop is an AI-generated straightaway feasibility asset, not a licensed production asset. Its workspace SHA-256 is `A3AFFDC12F88471F92047BFA060BA11D86BA615216CC095E894F15C2D0F8DE14`; rights clearance is unresolved.

## Browser evidence

All screenshots are real Chromium captures at DPR 1. Mobile captures scroll the track into view so the responsive Tactical Track proof is visible within the exact 390×844 viewport.

| Scenario | Viewport | Screenshot | SHA-256 |
| --- | ---: | --- | --- |
| Base | 1440×900 | `evidence/tactical-track/base-desktop.png` | `89AA1835AC4F2ABEB0870534D67D275C951B9F41BDD4A4B845C0EF346C78AB17` |
| Base | 768×1024 | `evidence/tactical-track/base-tablet.png` | `C7C3B435BA92AF357ABB46F5222C07CF863889C1845BA89590556B05C20284C3` |
| Base | 390×844 | `evidence/tactical-track/base-mobile.png` | `EFEA5FB806457069A15B0A543DA8609D58C9EA2A9383B56CE44F9044C3EDB221` |
| Contested lead | 1440×900 | `evidence/tactical-track/contested-desktop.png` | `5E120C9F680F2796EE29250526A54B8CBCA379409E70CC78F3D633568CB31B3B` |
| Contested lead | 768×1024 | `evidence/tactical-track/contested-tablet.png` | `079CF29DC8460BBB2E684C11ED2AC5095907F9F3086A6FD2AB6767DFA2CA83D2` |
| Contested lead | 390×844 | `evidence/tactical-track/contested-mobile.png` | `CEA17BA23580669195007AA5EB791A9C3065418F4B7A50A6CAF97ED613D45125` |

## Validation

- `pnpm --filter @racing-intelligence/web build` — PASS.
- Playwright interaction check — PASS: 11 runners present; Base → Contested lead changes runner position styles.
- Playwright load measurement — PASS: 1,577 ms in the measured local run.
- `@axe-core/playwright` — PASS: 0 violations after landmark correction.
- V7 handoff pack validator — PASS before lab work.

## Comparative visual review against V7

What is retained: cinematic turf depth, strong horizon/rail perspective, navy/gold HUD language, early-settling axis, grouped bands, selected-runner detail, analytical map, and prominent information caveats.

What remains gated: the backdrop and runner layers are generated feasibility assets with rights pending, and no human reviewer or owner has approved their use. The current candidate is materially above the superseded geometric treatment, but it is still a synthetic Phase 0 proof rather than licensed production artwork. GPU/3D work is not required for this layered feasibility test and remains out of scope until asset rights and reviewer direction are resolved.

## Decision

**Production HOLD remains.** The current visual candidate is suitable for continued Phase 0 review and no longer uses the rejected geometric runner treatment. It must not advance to production or sign-off until the synthetic assets are replaced or cleared, and genuine independent reviewer plus owner decisions are recorded. No deployment, provider activation, Auth0 change, wagering capability, or The Long Straight edit was performed.
