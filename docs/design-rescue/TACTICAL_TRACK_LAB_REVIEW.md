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

The runner field was iterated after the first review: the geometric SVG treatment was removed, photorealistic synthetic horse-and-jockey layers were added, and dense name pills were reduced to a selected-runner label plus numbered identity markers. All runners now use one shared visual scale per viewport so the side-on field reads consistently. Full runner names remain in the linked groups and detail panel so the track remains readable at mobile width.

The renderer now consumes a per-runner `silks` metadata object. This lab supplies synthetic local assets only; it does not activate or call Betfair. A production adapter can populate the same field from a rights-cleared provider-normalized silk asset or colour/pattern manifest.

The backdrop was then iterated from a bend to a straightaway, and finally to the correct side-on race view for the side-profile runner layers. Horizontal parallel rails now sit behind the field, leaving the compositing zone open so runners do not visually intersect the fence.

The analytical pace map was also corrected to follow the V7 golden language: four labelled settling bands, a gridded distance-to-finish axis, all eleven field members from the main track DOM, Base/Contested scenario movement, and the same selected-runner highlight instead of an unrelated four-dot placeholder.

The backdrop is an AI-generated side-on straightaway feasibility asset, not a licensed production asset. Its workspace SHA-256 is `E2465ADC12BACD63437EE79F5724C8B52AD3531576C24764DF7E947F730A741E`; rights clearance is unresolved.

## Browser evidence

All screenshots are real Chromium captures at DPR 1. Mobile captures scroll the track into view so the responsive Tactical Track proof is visible within the exact 390×844 viewport.

| Scenario | Viewport | Screenshot | SHA-256 |
| --- | ---: | --- | --- |
| Base | 1440×900 | `evidence/tactical-track/base-desktop.png` | `EDD02E10D86D4742BD96325B77346A13F42BF3CD74C21D7C55B0916549038121` |
| Base | 768×1024 | `evidence/tactical-track/base-tablet.png` | `EE8FAFE8824C80F0B6A4C27A9D229D1F87ED65028E808A0680F6566CBF6C3C30` |
| Base | 390×844 | `evidence/tactical-track/base-mobile.png` | `2BD87D8358164F7FDB333E5ED112E02B452AD059BC192A03AAB1F749BEFC95FB` |
| Contested lead | 1440×900 | `evidence/tactical-track/contested-desktop.png` | `CB13C0F64E8D41DB94859587BE7614592951F736AD42D08182402444A3D52BF1` |
| Contested lead | 768×1024 | `evidence/tactical-track/contested-tablet.png` | `3F0443C0B6EEF64F190588E7135A17BB1F6B2A223BE77DE4A899A698C7CD4CA7` |
| Contested lead | 390×844 | `evidence/tactical-track/contested-mobile.png` | `EA8235DAD578442FD6685B2267B89B60102217A85B4FB98B2440D9916C75F3AE` |

## Validation

- `pnpm --filter @racing-intelligence/web build` — PASS.
- Playwright interaction check — PASS: 11 runners present; Base → Contested lead changes runner position styles and linked pace-map positions; selecting runner 5 selects pace-map runner 5.
- Playwright load measurement — PASS: 1,577 ms in the measured local run.
- `@axe-core/playwright` — PASS: 0 violations after landmark correction.
- Direct-file smoke test — PASS: `file://` opening loads the backdrop and all 11 runner images; axe reports 0 violations.
- V7 handoff pack validator — PASS before lab work.

## Comparative visual review against V7

What is retained: cinematic turf depth, strong horizon/rail perspective, navy/gold HUD language, early-settling axis, grouped bands, selected-runner detail, analytical map, and prominent information caveats.

What remains gated: the backdrop and runner layers are generated feasibility assets with rights pending, and no human reviewer or owner has approved their use. The current candidate is materially above the superseded geometric treatment, but it is still a synthetic Phase 0 proof rather than licensed production artwork. GPU/3D work is not required for this layered feasibility test and remains out of scope until asset rights and reviewer direction are resolved.

## Decision

**Production HOLD remains.** The current visual candidate is suitable for continued Phase 0 review and no longer uses the rejected geometric runner treatment. It must not advance to production or sign-off until the synthetic assets are replaced or cleared, and genuine independent reviewer plus owner decisions are recorded. No deployment, provider activation, Auth0 change, wagering capability, or The Long Straight edit was performed.
