# Nexus V7 owner test build

Local preview: http://127.0.0.1:5201/

Hosted UAT preview: https://nexus-staging-frontend.onrender.com/

The hosted build has two explicit owner modes. `LIVE EVIDENCE` opens the licensed,
provider-backed read-only journey. `ANALYSIS LAB` opens the complete V7 visual
product using deterministic synthetic fixtures so every graph, table and
analytical surface can be exercised without implying that fixture values are
live racing evidence.

For the authenticated live-data UAT journey, use `LIVE EVIDENCE` in the hosted
preview and follow
`docs/deployment/LIVE_AUTHENTICATED_E2E_CHECKLIST.md`. The hosted lane is
private, owner-scoped, licensed, read-only, and wagering-disabled.

For the full visual/product journey:

1. Sign in to the hosted preview with the allowlisted owner account.
2. Choose `Analysis lab` in the `VIEW` control in the top-right of the shell.
3. Confirm the `OWNER ANALYSIS LAB` banner and `ANALYSIS LAB · SYNTHETIC_ONLY` badges.
4. Exercise the atlas in the order below. Every analytical surface should be
   available in this mode, including tactical track, speed map, runner
   comparison, model evaluation, markets, evidence, assistant, notebook,
   alerts, reports and settings.
5. Switch back to `Live evidence` and confirm the licensed live meeting flow
   returns with no synthetic replacement values.

## Approved atlas order

1. Command Centre
2. Meetings
3. Tactical Track
4. Runner Intelligence
5. Runner Comparison
6. Model Laboratory
7. Markets
8. Evidence
9. Research Assistant
10. Notebook
11. Watchlists
12. Alerts
13. Reports
14. Settings and Assurance

## Owner checks

- Compare the desktop and mobile screenshots in `docs/evidence/v7-implementation/` against the matching V7 pack reference.
- On Tactical Track, change the field size between 6, 11 and 14 runners, switch Contested Lead, and select a runner. The track and speed map should remain linked.
- On Evidence, open the receipt ledger action and switch Receipts/Rights/Timeline.
- On Alerts, switch Active/Recent/Rules and toggle an alert. No automatic action should appear.
- On Settings, open the assurance action and toggle Compact data tables or Reduce animated motion.
- In Analysis Lab, confirm the synthetic-only boundary remains visible on every screen and no fixture value is presented as live.
- In Live Evidence, confirm the licensed boundary remains visible and no unsupported analytical value is presented.
- Review at 1440×900, 768×1024 and 390×844 before approving the candidate.

## Current gate

Automated functional and responsive checks pass. Independent owner visual review is still required before this candidate can be called V7-approved or deployed.
