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

The backdrop was then iterated from a bend to a straightaway, and finally to the correct side-on race view for the side-profile runner layers. Horizontal parallel rails now sit behind the field, leaving the compositing zone open so runners do not visually intersect the fence.

The backdrop is an AI-generated side-on straightaway feasibility asset, not a licensed production asset. Its workspace SHA-256 is `E2465ADC12BACD63437EE79F5724C8B52AD3531576C24764DF7E947F730A741E`; rights clearance is unresolved.

## Browser evidence

All screenshots are real Chromium captures at DPR 1. Mobile captures scroll the track into view so the responsive Tactical Track proof is visible within the exact 390×844 viewport.

| Scenario | Viewport | Screenshot | SHA-256 |
| --- | ---: | --- | --- |
| Base | 1440×900 | `evidence/tactical-track/base-desktop.png` | `ECF37657E8F1728D6FF4281A4CFE78521D6A74765E43B2CCFACAE63BD3A4CBFE` |
| Base | 768×1024 | `evidence/tactical-track/base-tablet.png` | `F253312AAEBE6559FF5C548C72ACA587BBF05B6BC9F2162C9F0392387852DCE4` |
| Base | 390×844 | `evidence/tactical-track/base-mobile.png` | `119E2A29D8F3ED0867A137090802A5175B562739A48BAB39C7D23F6CCE171CFA` |
| Contested lead | 1440×900 | `evidence/tactical-track/contested-desktop.png` | `C8253F37A4AAD602F847A30BD8117B65FC3A4F9ED360D834F8ECFE6175B7481D` |
| Contested lead | 768×1024 | `evidence/tactical-track/contested-tablet.png` | `BFDAF86C51CCBCFC1714AA1FF33286D31A024D4587127B48B1AE6202D9C856B5` |
| Contested lead | 390×844 | `evidence/tactical-track/contested-mobile.png` | `706B32F0F0D1EEFF4644970FBD2A729433EA258E6125A7EE680B5A6EE255AA62` |

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
