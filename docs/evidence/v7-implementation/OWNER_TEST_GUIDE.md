# Nexus V7 owner test build

Local preview: http://127.0.0.1:5201/

This is a synthetic-only, read-only visual candidate. It does not activate Render, Auth0, racing-provider credentials, wagering, or The Long Straight.

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
- On every screen, confirm the synthetic-only / rights boundary remains visible and no unsupported racing value is presented as live.
- Review at 1440×900, 768×1024 and 390×844 before approving the candidate.

## Current gate

Automated functional and responsive checks pass. Independent owner visual review is still required before this candidate can be called V7-approved or deployed.
