# Race-level evaluation metrics

RIL-028 reports implementation metrics only over official synthetic results. A report records `N`, UTC time range, code segments, horizon, model version, missingness counts, deterministic 95% percentile-bootstrap intervals and calibration bins.

- Log loss is the mean `-ln(p_winner)` across races.
- Multiclass Brier score is the mean `sum((p_i-y_i)^2)` across the complete field.
- A zero-probability observed winner produces infinite log loss; it is not clipped or silently repaired.
- Calibration bins use every runner probability and a one-hot observed-winner target.
- The report is labelled `IMPLEMENTATION_METRICS_SYNTHETIC_ONLY` with `validated_claim: false`.

The fixed synthetic report is `fixtures/synthetic/metrics_b1_v1.json`; verify it with:

```powershell
.venv\Scripts\python.exe scripts/generate_metric_report.py
```

