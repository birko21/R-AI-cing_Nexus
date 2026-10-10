# RIL-077 historical sample and reconciliation specification

## Proposed first sample

Request a bounded Australian thoroughbred sample covering at least 24 consecutive months, with a minimum target of 10,000 completed races where available. Stratify by venue, distance bands, race type/class and field size; retain all eligible runners, scratchings and abandoned-race status. The first sample is research-only and must be delivered with contemporaneous pre-race observations, not reconstructed from post-race outcomes.

Required entities and fields:

- meeting, race and runner identifiers with source namespace;
- scheduled start, publication/observation/retrieval timestamps and timezone;
- field status, barrier, distance, venue, surface/going and race class;
- runner name plus jockey/trainer and prior form where licensed;
- historical results, finish status and dead-heat/scratching/abandonment markers;
- speed, rating and sectional fields only when source definitions and timestamps are documented;
- pre-race fixed or exchange prices, movement snapshots and available/matched volume only when explicitly licensed;
- source receipt identifier, response hash and deletion/retention classification.

The requested permission must separately name raw retention, derived features, training, calibration, evaluation, fair-price derivation and local display. A personal-use permission in The Long Straight is not sufficient.

## Provider route and cost status

| Provider | Intended role | Cost evidence | Rights status | Decision |
|---|---|---|---|---|
| PuntersEdge | Thoroughbred historical form/results and settled fixed prices | Personal free-plan probe only; not a quote or transferable entitlement | Application-specific retention/model/display rights missing | Request written bounded export quote and licence |
| Krok Odds | Form/market enrichment and possible authorised historical results | Reported free tier and paid historical range; observed account tier did not prove free access | Historical retention and model-use rights missing | Request written sample, price and rights confirmation |
| FormFav | Field/catalogue, barrier and participant enrichment | Not stated in audited evidence | No R-AI-cing rights or durable history established | Defer unless field-only rights are sufficient |
| Betfair Exchange | Pre-race exchange prices, movement, depth and matched volume | Cost/data entitlement not established | Read-only market-data, historical, liquidity, SP, retention, training and display rights missing | Separate later approval; synthetic adapter only |

There is no confirmed lowest-cost legitimate route. Krok has the lowest documented nominal tier, but its historical access and rights are unresolved. PuntersEdge is the lowest-friction bounded form/results candidate only if a new written licence is cheaper and grants the required rights. No purchase is authorised by this document.

## Reconciliation tests before acceptance

1. Confirm counts and unique `(provider, meeting, race, runner)` identities; reject duplicate runner records.
2. Verify provider namespaces are never joined on names alone; require stable IDs or a documented multi-field identity match and retain conflict reports.
3. Confirm every pre-race field has an observation/publication timestamp at or before the race cutoff; reject unknown timestamp semantics for modelling.
4. Verify results and starting prices are post-race labels only and cannot enter pre-race features.
5. Reconcile race dates, venues, distances, barriers/boxes, participant names and outcomes across an agreed sample; report missingness without silent imputation.
6. Compare price snapshots to their receipt timestamps, distinguish bookmaker fixed prices from exchange back/lay prices, and require explicit liquidity units.
7. Hash raw receipts and the complete feature snapshots; verify a separately held manifest before training.
8. Confirm retention/deletion, backup, display, derived-output, training and evaluation permissions in writing before storing or processing the sample.

## Code gaps

No harness or greyhound historical coverage is contractually evidenced by the audited four-provider material. Separate acquisition and rights work is required for harness and greyhound; thoroughbred approval must not be generalized to either code.
