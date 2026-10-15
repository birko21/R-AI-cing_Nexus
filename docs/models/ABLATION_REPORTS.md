# Synthetic ablation reports

`services/api/app/ablation.py` compares a baseline and one incremental
feature/provider lane on the same chronological holdout. The report includes
race-level log loss, multiclass Brier score, calibration, deterministic
bootstrap intervals, missingness, coverage and a leakage-safe report hash.

The report is explicitly `IMPLEMENTATION_METRICS_SYNTHETIC_ONLY`, sets
`validated_claim` to `false`, and has no promotion authority. A model remains
`HOLD` until separate calibration, independent assurance and owner approval
records exist.
