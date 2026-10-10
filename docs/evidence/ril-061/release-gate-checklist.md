# RIL-061 release evidence

## Scope

Historical feature contracts, offline B0–B4 benchmark contracts, walk-forward evaluation reporting, deterministic forecast explanations and provider readiness verdicts.

## Evidence

- `research-output.json` — synthetic sample research output and limitations.
- `model-evaluation.json` — synthetic evaluation report with segments, ablation, calibration and market comparison fields.
- `provider-readiness.json` — executable code/provider verdicts.
- `b3-synthetic-evaluation.json` — pinned LightGBM/CatBoost synthetic training, artifact and evaluation evidence.
- `research-workbench.png` — browser evidence for model comparison and feature availability.
- `validation-record.md` — local commands and exit codes.
- `services/api/tests/test_historical_features.py`
- `services/api/tests/test_model_benchmarks.py`
- `services/api/tests/test_historical_evaluation.py`
- `services/api/tests/test_explainability.py`
- `services/api/tests/test_provider_readiness.py`

## Gate result

`RIL-061 = PARTIAL_SAFE_FOUNDATION`

The architecture now supports evidence-rich historical features and evaluation contracts for all three codes. Pinned B3 LightGBM and CatBoost backends execute against synthetic specialist inputs, but every result remains `ILLUSTRATIVE_SYNTHETIC_ONLY`. No provider is approved, no external connectivity is enabled, and no predictive-validity claim is made.

## Independent assurance assertions

- [x] Forecast inputs are filtered by observation, publication, retrieval and explicit pre-race eligibility timestamps.
- [x] Synthetic Betfair starting price is represented only as a post-race observation and is rejected by pre-race explanation/feature paths.
- [x] Forecast probabilities are validated at race level and coupled fields abstain.
- [x] Provider identity conflicts and duplicate eligibility timestamps are excluded rather than overwritten or imputed.
- [x] Model status is fixed to `ILLUSTRATIVE_NOT_VALIDATED`; no synthetic result can promote a model.
- [x] Provider credentials and external connectivity remain outside the implementation; no frontend or log path receives provider secrets.
- [x] The Long Straight was audited read-only and remains unchanged.
- [x] No wagering, automated staking, order or trading functionality was introduced.

Observed assurance commands: backend tests, Ruff, contract validation, synthetic B3 generation, web typecheck/build and six browser smoke tests passed; repository validation and security audit passed. The exact commands and exit codes are recorded in `validation-record.md`.

## Required next gate

`RIL-077 = Approved historical dataset acquisition`, requiring owner-approved provider rights, retention/model-use terms and a historical dataset with contemporaneous timestamps. The B3 dependency decision is now recorded and pinned.
