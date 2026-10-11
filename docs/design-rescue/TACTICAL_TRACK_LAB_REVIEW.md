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

The backdrop is an AI-generated feasibility asset, not a licensed production asset. Its workspace SHA-256 is `C23F7D0D8426B683C27C4B2EFF7194F1D21FBAB6A47AC213FDFB32F048BFA8F9`; rights clearance is unresolved.

## Browser evidence

All screenshots are real Chromium captures at DPR 1. Mobile captures scroll the track into view so the responsive Tactical Track proof is visible within the exact 390×844 viewport.

| Scenario | Viewport | Screenshot | SHA-256 |
| --- | ---: | --- | --- |
| Base | 1440×900 | `evidence/tactical-track/base-desktop.png` | `32D3F49D88453BD3D7A9BBD3DCB166E42018D8BB4D5DF8D2C2D20D3D291592DF` |
| Base | 768×1024 | `evidence/tactical-track/base-tablet.png` | `83BBA8A4DA749C60FD7CD1FC802B7ADE5B8A79BD4FA7CB8BF68F86F323F898C5` |
| Base | 390×844 | `evidence/tactical-track/base-mobile.png` | `22B0CB3218EC758E850AD9787077DDDE35CDEA389B72182BB07BC28D7430145A` |
| Contested lead | 1440×900 | `evidence/tactical-track/contested-desktop.png` | `E381FC409B62BD24A2CA08D09E2F8323B3017B4BF8EA827CD1A6B5DD818D461B` |
| Contested lead | 768×1024 | `evidence/tactical-track/contested-tablet.png` | `ED705580B27AD834B1D484B02D2196EE8DBDD14DBFEF13E1FE06B72F00195CFC` |
| Contested lead | 390×844 | `evidence/tactical-track/contested-mobile.png` | `302F2103CBEC1A18F96369BD60F4D5289989BE54586519907874FC6D2343EA50` |

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
