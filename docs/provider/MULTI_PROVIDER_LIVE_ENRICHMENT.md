# Multi-provider live enrichment

## Objective

Build one real-data race analysis surface from complementary provider evidence.
No provider is treated as a complete racing dataset and no missing provider
value is replaced with synthetic content.

## Source responsibilities

| Provider | Intended enrichment | Boundary |
| --- | --- | --- |
| FormFav | Australian thoroughbred meeting/card fields, barriers, weights, jockeys, trainers, form and scratch state | Card/form fields must be reconciled to the canonical race and runner before display or modelling. |
| PuntersEdge | Prior runner history, settled results and fixed Win/Place observations | Results are labels; they are never used before their publication or race cutoff. |
| Krok Odds | Meeting board, odds enrichment, runner history, sectionals and results where returned | Krok-generated predictions remain an external benchmark, not a Nexus training feature. |
| Betfair Exchange | Exact exchange market identity, back/lay prices, available size, matched liquidity and movement snapshots | SP is post-race evidence; catalogue and market-book captures are separate operations. |

## Canonical flow

```text
provider response
  -> immutable licensed receipt
  -> provider-specific normaliser
  -> exact race/runner/market reconciliation
  -> quarantine on conflict, missing identity or bad time
  -> as-of feature materialisation
  -> form-only + market-only + combined calibrated probabilities
  -> read-only visual analysis
```

Every accepted value carries its provider, source receipt, observation time,
publication time where available, rights state, quality state and identity
evidence. Cross-provider agreement increases coverage; it does not erase
conflicts.

## Implemented in this pass

- Krok requests now use the provider's `race_type` vocabulary, request tote
  and exchange lines, and substitute dated result paths correctly.
- Generic live projection recognises Krok-style jump-time, race-number,
  horse-code, slug and scratch fields without inventing a timestamp.
- Betfair market-book parsing now validates publish time, exact selection IDs,
  back/lay ladders, matched liquidity, market status and in-play state.
- Betfair catalogue projection now creates exact market-selection mappings.
- Betfair book captures can be projected into the append-only `market_quotes`
  table with quarantine for unmapped selections.
- Render now declares non-secret approval configuration fields for all four
  providers while keeping every provider disabled by default.

## Remaining activation gates

1. Provider-specific approval records and enabled flags must be configured in
   Render for the operations actually permitted by each account.
2. A real provider response must pass the normaliser and reconciliation tests.
3. The card/form pipeline must be populated before a combined model can claim
   a probability; a single target-day card is UAT data, not a training set.
4. Betfair market-book capture requires a prior catalogue capture and exact
   market mappings.
5. Historical retention and chronological walk-forward evaluation are required
   before promoting a model from `NOT_TRAINED` or `ILLUSTRATIVE_ONLY`.

## Target-card acceptance

For the requested 17 October 2026 Randwick and Caulfield cards, acceptance is:

- all available meetings, races and runners are provider-backed;
- each runner has a canonical identity or an explicit quarantine reason;
- each market quote has exact market and selection mapping;
- no SP, result, or post-race sectional is used before the race cutoff;
- the UI shows source, freshness, coverage and conflicts;
- no synthetic card is shown as a fallback;
- model output is labelled unavailable until real-data calibration evidence
  exists.
