# B1 form heuristic contract

`B1_FORM_HEURISTIC` is a deterministic, code-aware illustrative baseline. It is not validated and must not be described as predictive of live racing.

## Inputs and cutoff

- Active eligible entries and exact field revision.
- Historical runs for the entry's participant, each with observed time, distance and finish position.
- Target race distance and a UTC forecast cutoff.
- Only runs with `observed_at < cutoff` are eligible; later facts are excluded.
- A race abstains if any active eligible runner has fewer than two usable historical runs.

## Features and weighting

Each usable run contributes a finish-form score `1 / finish_position`, a distance-match score (`1.0` exact, `0.5` within 200m, otherwise `0.0`) and an exponentially decayed recency score. The code-specific weights are:

| Code | Form | Distance | Recency | Half-life |
| --- | ---: | ---: | ---: | ---: |
| Thoroughbred | 0.55 | 0.30 | 0.15 | 30 days |
| Harness | 0.50 | 0.35 | 0.15 | 45 days |
| Greyhound | 0.45 | 0.20 | 0.35 | 21 days |

The weighted score receives fixed additive smoothing of `0.1`, then probabilities are normalized across active eligible runners. Scratched and reserve entries do not receive a forecast row.

Invalid fields, unsupported codes or modes, coupled entries, missing target distance, insufficient support, duplicate/invalid inputs and non-finite calculations abstain with a diagnostic reason. Every output records the model ID/version, weights, smoothing, minimum support, field revision, cutoff, source fixture checksum, data mode and `ILLUSTRATIVE_NOT_VALIDATED` status.

The fixed-seed replay artifact is `fixtures/synthetic/forecasts_b1.json`; verify it with:

```powershell
.venv\Scripts\python.exe scripts/generate_b1_forecast_manifest.py
```

