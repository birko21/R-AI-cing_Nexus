# PR #75 closure and RIL-077 readiness

## PR governance result

PR #75 was confirmed CI-green at the requested commit `352d3190e83f7973bf49d9823e0308b99d0f5221`. The PR run `38032861543` passed backend, contracts/security/synthetic evaluation, frontend and browser smoke; duplicate push run `38032858839` also passed. The PR is open and unmerged, with no independent reviews, no review requests, and no recorded review decision. GitHub exposed no `main` branch protection or repository ruleset through the authenticated API.

Merge readiness: **BLOCKED_PENDING_INDEPENDENT_REVIEW**. The implementation cannot self-satisfy an independent approval. No merge, approval impersonation, branch-protection bypass or production deployment was performed.

The final governance record is deliberately not chased with repeated evidence-only commits. The immutable CI evidence remains tied to the exact tested SHA; later documentation must identify itself as a separate governance change.

## Statistical readiness

The LightGBM, CatBoost and race-level conditional-choice challengers remain intact. The synthetic generator now uses chronological training, held-out calibration and test windows, exact fold membership, feature snapshot provenance and retrained ablation challengers.

Synthetic fixtures are outcome-informed: runner signals and winners are constructed together, synthetic Betfair prices are deterministic, and the sample is not representative of racing populations, source latency, missingness, market formation or provider rights. Therefore synthetic log loss, Brier, calibration or ranking results cannot support a real-world accuracy, profitability or `MODEL_VALIDATED` claim.

Project minimum before any real-data comparison is considered credible:

- 5,000 completed races per code, with 10,000 preferred; all runners, scratchings and non-standard outcomes retained and separately reported.
- Chronological 60/20/20 train/calibration/test allocation, with at least 1,000 calibration and 1,000 test races per code.
- At least 100 races in each reported track, distance, race-type and field-size segment; otherwise report the segment as insufficient.
- At least 2,000 common test races for any market-vs-form comparison, with contemporaneously available prices and timestamp evidence.
- Walk-forward results from at least three temporal test windows, independent artifact and dataset hashes, confidence intervals, missingness sensitivity and feature-family/provider ablations.
- No promotion unless out-of-sample results are stable across windows, calibrated on held-out data, independently assured and approved in the model registry.

## Acceptance suite

`historical_acceptance.py` provides an offline receipt gate that rejects missing/naive timestamps, post-race observations, unapproved rights, weak identity evidence, invalid payload hashes and duplicate provider runner records. Historical ingestion must additionally pass the reconciliation checklist in `RIL077_HISTORICAL_SAMPLE_SPEC.md` before any approved receipt enters feature generation.

Leakage canaries assert that post-race values cannot alter a pre-race feature snapshot. Existing tests also quarantine future publication/retrieval, unapproved rights, provider identity conflicts and duplicate eligibility timestamps.

## Remaining external decisions

- Independent GitHub reviewer approval for PR #75.
- Written provider terms for RIL-077 naming R-AI-cing Nexus.
- Owner-approved cost ceiling and any subscription or export expenditure.
- Explicit raw retention, feature engineering, training, calibration, evaluation, derived forecast and display rights.
- Separate harness and greyhound acquisition and licensing decisions.

No provider connectivity, credentials, purchase, public deployment, wagering, staking or trading functionality is enabled. The Long Straight remains unchanged.
