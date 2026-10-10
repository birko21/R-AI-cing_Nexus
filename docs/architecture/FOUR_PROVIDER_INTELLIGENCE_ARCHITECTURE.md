# Four-provider intelligence architecture

## Target shape

The roadmap extends the existing local modular monolith with a source-neutral intelligence lane:

```text
provider evidence + entitlement registry
              |
      disabled-by-default adapters
              |
 raw envelopes / checksums / bitemporal receipts
              |
 canonical race + exact runner identity resolver
              |
  as-of feature materialization and quarantine
       /             |              \
 form-only       market-only       combined
 specialists    specialists       specialists
       \             |              /
 race-normalised probabilities -> calibration -> independent assurance
```

The browser and existing API remain local-first. Providers never write directly to canonical race state or model tables. A successful provider read produces an immutable receipt; an explicit reconciliation step may then map a provider race and runner to the canonical field. Name-only joins, duplicate runner identities, unverified timestamps and post-race fields fail closed.

## Provider adapter boundary

The existing `ProviderCapabilities`, `ContractedProviderAdapter`, `RawEnvelope`, exact market mapping, `MarketHistory` and source-approval gate remain the controlling contracts. The capability matrix adds governance evidence that the current runtime contract intentionally does not infer: endpoint scope, cost, historical depth, reliability, retention, display rights and model-training rights.

Each future real adapter must have:

- a provider-specific transport/parser module;
- an allowlisted endpoint and operation declaration;
- a source receipt with `retrieved_at`, `first_observed_at`, optional provider publication time, checksum, data mode and rights state;
- exact code/race/field/entry/market/selection identity;
- bounded time, body size, concurrency and quota behaviour;
- a reconciliation report and source-health monitor;
- an independent licensing record before activation.

## Betfair first-class market lane

Betfair is represented as a full market-intelligence source, not as a hidden odds field:

1. **Catalogue:** market ID, market name/type, venue, scheduled start, code classification and runner catalogue.
2. **Identity:** selection ID is retained alongside the canonical entry mapping; runner names are descriptive labels, never identity keys.
3. **Read-only book:** back/lay prices, available size and matched/liquidity values are stored as timestamped observations when the authorised endpoint returns them.
4. **Historical movement:** every repeated snapshot or licensed historical observation is append-only and reconstructable as-of a forecast cutoff.
5. **Starting price:** SP is a separate post-race/settlement observation. It can support outcome diagnostics or a separately authorised target, but is excluded from pre-race features at any earlier cutoff.
6. **Market state:** suspended, removed, closed, incomplete and stale states remain explicit; a missing book is not an empty market.

The current implementation of this roadmap stops at a synthetic, read-only fixture. It deliberately does not implement login, streaming, order placement, staking, trading or real outbound connectivity.

## Data and model flow

Source-specific observations are kept separate from canonical entities until exact identity and temporal checks pass. Feature materializers receive a race cutoff and may consume only observations where both source time and receipt time are at or before that cutoff. Race-level normalisation happens after field membership and duplicate checks, not before.

Provider contribution is evaluated in nested comparisons:

- strong code-specific baseline;
- form-only specialist;
- market-only specialist;
- combined specialist;
- combined specialist with one additional provider or feature family.

The evaluation record must preserve split-manifest hash, feature schema version, provider evidence versions, sample counts, coverage/missingness, log loss, Brier score, calibration error and predictive-value analysis. A positive point estimate without uncertainty, temporal holdout evidence and independent assurance is not an improvement claim.

## Safety state

The active R-AI-cing Nexus data mode remains `SYNTHETIC_ONLY`. Real FormFav, PuntersEdge, Krok and Betfair adapters are disabled until their individual approval records pass. No provider availability is allowed to unlock wagering, staking, trading, settlement or automatic actions.
