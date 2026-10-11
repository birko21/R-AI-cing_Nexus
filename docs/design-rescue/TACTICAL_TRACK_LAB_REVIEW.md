# Tactical Track Feasibility Lab Review

**Status:** HOLD
**Scope:** Tactical Track only; no approval for the remaining 13 workspaces.
**Draft PR:** https://github.com/birko21/R-AI-cing_Nexus/pull/177
**Lab URL:** `http://127.0.0.1:5173/tactical-track-lab.html`

## Candidate delivered

The lab is a standalone public HTML entry, not a production route. It uses one synthetic fixture with eleven independently positioned SVG runner layers over a runner-free generated turf backdrop. The same fixture supports:

- Base case and Contested lead scenarios;
- visible inside rail, start/finish axis, 0–400 m early-settling framing, and two- to three-abreast groups;
- selected-runner detail, evidence caveat, and linked analytical pace-map treatment;
- responsive desktop, tablet, and mobile layouts;
- explicit synthetic/illustrative and rights-pending labels.

The backdrop is an AI-generated feasibility asset, not a licensed production asset. Its workspace SHA-256 is `C23F7D0D8426B683C27C4B2EFF7194F1D21FBAB6A47AC213FDFB32F048BFA8F9`; rights clearance is unresolved.

## Browser evidence

All screenshots are real Chromium captures at DPR 1. Mobile captures scroll the track into view so the responsive Tactical Track proof is visible within the exact 390×844 viewport.

| Scenario | Viewport | Screenshot | SHA-256 |
| --- | ---: | --- | --- |
| Base | 1440×900 | `evidence/tactical-track/base-desktop.png` | `62CD94C4F54BA149A827876A36B75BEFD7B9E5FDE4BA2435A9DEAFF7A7C06F9B` |
| Base | 768×1024 | `evidence/tactical-track/base-tablet.png` | `F8EADF941D70B953FD18B8F61C8B560C52DAB829A7E5877B78E5757993D45BB4` |
| Base | 390×844 | `evidence/tactical-track/base-mobile.png` | `BCF457C0D09F082D5B083486B878E6F9A9D29CB59B43DC2A0694A7ACD7C85B35` |
| Contested lead | 1440×900 | `evidence/tactical-track/contested-desktop.png` | `C13A71D2F86523A06832D240A486E309B63DB04BE057DDB239C856B46F15A42B` |
| Contested lead | 768×1024 | `evidence/tactical-track/contested-tablet.png` | `D84B6FB135EC6D243257151F6AC9EA0F955CCE2C66938A5817DC60C20C03D643` |
| Contested lead | 390×844 | `evidence/tactical-track/contested-mobile.png` | `ED029158EFAE81F4C130E586F6F088B4CD8BE8D7B0F4D2069CD0B9D05B2CDD8C` |

## Validation

- `pnpm --filter @racing-intelligence/web build` — PASS.
- Playwright interaction check — PASS: 11 runners present; Base → Contested lead changes runner position styles.
- Playwright load measurement — PASS: 1,057 ms in the measured local run.
- `@axe-core/playwright` — PASS: 0 violations after landmark correction.
- V7 handoff pack validator — PASS before lab work.

## Comparative visual review against V7

What is retained: cinematic turf depth, strong horizon/rail perspective, navy/gold HUD language, early-settling axis, grouped bands, selected-runner detail, analytical map, and prominent information caveats.

What is below V7: the SVG runner sprites are simplified geometric feasibility shapes rather than realistic independently placeable horse/jockey assets; labels become dense at mobile width; no GPU/3D challenger was produced; and the backdrop is generated feasibility art with rights pending. The current lab therefore does not meet the V7 “match or exceed” quality bar for production.

## Decision

**HOLD for Tactical Track implementation.** The layer and responsive mechanics are feasible, but this candidate must not advance to production or sign-off. Next work requires owner-approved/licensed cinematic assets, substantially more realistic code-specific runner assets, a practical 3D/GPU comparison where useful, and genuine independent reviewer plus owner decisions. No deployment, provider activation, Auth0 change, wagering capability, or The Long Straight edit was performed.
