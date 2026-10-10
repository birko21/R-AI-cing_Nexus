# RIL-061 statistical benchmarks and evaluation

`services/api/app/model_benchmarks.py` implements the safe offline benchmark surface:

- **B0:** equal probability over active, eligible, uncoupled runners;
- **B1:** code-specific weighted form features with no imputation;
- **B2:** market-implied probabilities, normalised for overround and using exchange back/lay midpoint when both sides exist;
- **B3:** explicit LightGBM/CatBoost availability contract; missing engines fail closed and are not replaced silently;
- **B4:** log-linear combination of B1 and B2, marked uncalibrated until calibration evidence exists.

`services/api/app/historical_evaluation.py` scores chronological test cases with log loss, Brier score, calibration bins, top-ranked accuracy, code/track/distance/race-type segments, missing-input sensitivity, market comparison, feature-family ablations and fold evidence. Dead heats, scratchings, abandoned races, coupled entries, non-test folds and invalid fields are excluded with reasons.

The existing walk-forward splitter remains the source of train/calibration/test windows. The generated RIL-061 sample is synthetic-only and labelled `ILLUSTRATIVE_SYNTHETIC_ONLY`; it is not evidence of real-world accuracy, calibration or profitability. Price-based simulation remains out of scope until contemporaneous licensed prices and realistic cost assumptions are available.
