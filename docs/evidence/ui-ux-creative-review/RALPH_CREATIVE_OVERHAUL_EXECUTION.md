# Ralph creative overhaul execution log

Date: 2026-10-15  
Branch: `codex/live-provider-staging`

## Discovery completed

- Compared the current implementation to the approved workspace-atlas desktop,
  tablet and mobile captures.
- Reviewed the existing visual review HOLD, the sprint tickets NXD-012–019 and
  the no-wagering/data-mode ADR.
- Audited the hosted Render entry boundary and confirmed the current service,
  branch and deploy workflow.
- Audited the React shell, authenticated boot path, workspace routing, live
  boundary, state language, responsive CSS, tests and evidence captures.

## Design decisions

- Preserve the horizontal workspace atlas and shared context from the agreed
  design rather than introducing a different information architecture.
- Give the product a distinctive Nexus research-OS identity: geometric mark,
  instrument grid, orbit geometry, editorial headings and evidence-led state
  colors.
- Make licensed startup neutral until the provider mode is known. Synthetic
  content must not flash during an authenticated live boot.
- Replace repeated synthetic workspace placeholders with individual preview
  compositions; make Evidence match the agreed provenance reference and make
  Tactical Track visibly side-on with a linked pace readout.
- Keep all visuals read-only, source-labelled and explicit about synthetic,
  unavailable, illustrative and no-wagering boundaries.

## Execution passes

| Pass | Commit | Result |
|---|---|---|
| Creative system and trust boundary | `f064c1f` | Nexus mark, branded shell, instrument grid, new loading boundary, workspace preview language, responsive/reduced-motion treatment. |
| Authenticated entry coherence | `9d8138e` | Auth0 sign-in, denied and expired-session surfaces use the same Nexus creative system. |
| Reference workspace depth | `ce232cf` | Evidence provenance composition, Tactical Track visual surface, expanded browser assertions and refreshed visual evidence. |

## Automated proof

- `npm run web:check` — PASS
- `npm run web:test -- --run` — PASS, 5 tests
- `npm run web:build` — PASS
- `$env:WEB_PORT='5177'; $env:PLAYWRIGHT_REUSE_SERVER='false'; pnpm web:e2e` — PASS, 6 tests
- Browser assertions now cover the Evidence shared context, provenance claim,
  not-live callout, and Tactical Track / linked pace map.
- Reduced-motion CSS handling is present and the existing axe/focus assertions
  remain green.

## Hosted proof

- Render frontend service: `nexus-staging-frontend`
- Latest commit: `ce232cf`
- Latest deploy: `dep-db8bvj59fdbs73cc5avg`
- Render status: `Deploy succeeded | Live`
- Hosted entry screen visually verified at
  `https://nexus-staging-frontend.onrender.com/`: Nexus brand mark, private
  owner access card, read-only/no-wagering/provenance boundary.

## Final authenticated hosted gate

Manual owner sign-in was completed in the browser. The hosted pass then verified:

- `https://nexus-staging-frontend.onrender.com/callback` resolves to an active
  owner session with `LIVE READ-ONLY`, `LICENSED` and `API READY` status.
- The command centre renders two provider-backed meetings from `punters-edge`,
  with a healthy ingestion monitor, `GET_RESULTS`, 2 meetings, 2 races, 21
  entries and 3 results.
- A reload begins in the neutral authenticated boot state and resolves to the
  licensed dashboard without rendering `DEMO ONLY`, `SYNTHETIC_ONLY` or
  fictional records during the live boot.
- Northam opens into the canonical Race 8 detail: 12 entries, 9 active, 3
  scratched, receipt verified, and an explicit statement that provider payloads
  and forecasts are not displayed.
- The visual hierarchy holds at the hosted desktop viewport: Nexus identity,
  workspace atlas, control deck, live ingestion monitor, provider cards, live
  detail, receipt proof and read-only capability boundary are all coherent in
  one research-OS system.
- Responsive repository evidence covers the agreed mobile breakpoint
  (`390x844`) for the command centre and research workbench, with the existing
  tablet workspace-atlas capture retained in `ril-018`.

## Final creative gate

`AAA: PASS` for the agreed creative/UI/UX overhaul and hosted owner experience.

The creative gate is complete because the design system is implemented,
automated and responsive evidence is green, the hosted owner path is visibly
provider-backed, the authenticated boot has no synthetic flash, and the live
detail preserves the agreed evidence-first/read-only boundary. Product
capabilities that are intentionally not enabled in this staging lane—forecasts,
markets, exports and wagering—remain clearly labelled as unavailable rather
than being represented as finished functionality.
