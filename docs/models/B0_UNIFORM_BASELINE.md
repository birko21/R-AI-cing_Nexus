# B0 uniform baseline

RIL-021 implements `B0_UNIFORM` as a deterministic, race-normalised baseline for the offline synthetic fixture.

For a valid field, let `n` be the number of active, eligible, non-coupled runners. Each eligible runner receives `1/n`; scratched and reserve entries receive no forecast row. The probabilities sum to one and the forecast records the exact field revision, UTC cutoff, source fixture checksum, model ID, model version and `SYNTHETIC_ONLY` mode.

The baseline fails closed with `ABSTAIN` for invalid or incomplete fields, coupled entries, unsupported outcomes, duplicate entry IDs, non-finite probabilities or unsupported data modes. `NO_RACING` is represented as `NOT_AVAILABLE`. The implementation is illustrative and explicitly not validated as a real-world predictor.

The reproducible fixture manifest is `fixtures/synthetic/forecasts_b0.json`. Verify it with:

```powershell
.venv\Scripts\python.exe scripts/generate_b0_forecast_manifest.py
```

