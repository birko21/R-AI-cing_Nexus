# ADR-0003: Permanent no-wagering boundary and explicit data modes

- **Status:** Accepted
- **Date:** 10 October 2026
- **Scope:** Product, API, UI, integrations and research tools

## Decision

The application is read-only research and decision support. It must not store bookmaker credentials, expose order or staking endpoints, submit bets, execute trades, or contain a hidden wagering path.

All data carries an explicit mode. G0–G3 uses `SYNTHETIC_ONLY`. Any later public-web adapter uses `SCRAPED_PUBLIC` and remains distinct from licensed/official data. No mode may be presented as current, official, licensed or validated without evidence.

## Consequences

- The UI uses research actions such as `Save selection`, `Compare` and `PASS`, never bet-placement calls to action.
- Synthetic and scraped records are excluded from validated-performance claims unless a later gate proves rights and temporal suitability.
- Static scans, route allowlists and negative network tests are release evidence.

