# Live release evidence packet

Date: 2026-10-15

This packet records the first real hosted, authenticated, read-only live-data
journey. It contains bounded labels, aggregate counts, deployment IDs,
workflow IDs, commit IDs, and HTTP status codes only. No credentials, tokens,
raw provider responses, or browser storage state are retained.

## Automated safe verification

Command:

```powershell
pwsh -File scripts/verify_live_release.ps1
```

Observed result:

```text
RESULT                 : PASS
DATA_MODE              : LICENSED
PERSISTENCE            : postgres
INGESTION_STATUS       : HEALTHY
PROVIDER               : punters-edge
OPERATION              : GET_RESULTS
MEETINGS               : 2
RACES                  : 2
ENTRIES                : 21
RESULTS                : 3
WAGERING_ENABLED       : False
PROTECTED_MEETINGS_HTTP: 401
FRONTEND_HTTP          : 200
FRONTEND_MONITOR       : present
RAW_STATUS_PAYLOAD     : absent
```

## Deployment and scheduler evidence

- Frontend commit `cefeebf` deployed successfully as Render deploy
  `dep-db8b1erncjis73f9676g`; Render reported a successful production build
  and live site.
- API deployment was already live on the licensed staging service.
- GitHub Actions workflow run `38723784884` on `main` completed successfully;
  the bounded provider job completed in 12 seconds.
- The safe status response after the workflow run reported `HEALTHY` coverage
  for 2 meetings, 2 races, 21 entries, and 3 results.

## Authenticated browser evidence

- Owner Auth0 sign-in completed in the hosted browser.
- The dashboard showed `LIVE READ-ONLY LICENSED API` and the live ingestion
  monitor with `HEALTHY` status.
- Two licensed meeting cards were visible. Northam opened to Race 8 with an
  official field revision and 12 canonical entries: 9 active and 3 scratched.
- The live view stated `LIVE RESEARCH VIEW · READ-ONLY`, `LICENSED`, and
  `WAGERING DISABLED` and stated that provider payloads and forecasts were not
  displayed.
- Sign-out returned to `Nexus owner sign-in required`.
- A post-logout request to `GET /v1/meetings` returned `401`.

## Release boundary

This evidence proves the licensed read-only provider-to-Neon-to-API-to-Auth0
browser path. Forecasts, markets, Betfair liquidity, wagering, provider
expansion, historical/model training, and production customer access remain
out of scope.
