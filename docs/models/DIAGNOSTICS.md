# Forecast diagnostics contract

RIL-029 keeps probability output separate from evidence strength. A diagnostic result reports the unchanged probability map plus support count, coverage, missingness reasons, model disagreement, OOD score/warning, evidence strength and configured abstention reasons.

Defaults are minimum support `2`, maximum model disagreement `0.20` absolute probability difference and maximum OOD score `0.50`. Missingness, disagreement and OOD warnings are abstaining conditions by default. Evidence strength is `HIGH` when no warning is present, `MEDIUM` for non-abstaining warnings, `LOW` when a configured warning causes abstention, and `INSUFFICIENT` when support is below threshold.

The deterministic diagnostic fixture is `fixtures/synthetic/diagnostics_v1.json`; verify it with:

```powershell
.venv\Scripts\python.exe scripts/generate_diagnostics_fixture.py
```

