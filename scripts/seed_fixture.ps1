$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Run pnpm bootstrap before seeding fixtures.' }
& '.venv\Scripts\python.exe' scripts/generate_synthetic_fixtures.py --check
if ($LASTEXITCODE -ne 0) { throw "Synthetic fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_b0_forecast_manifest.py
if ($LASTEXITCODE -ne 0) { throw "B0 forecast manifest validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_b1_forecast_manifest.py
if ($LASTEXITCODE -ne 0) { throw "B1 forecast manifest validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_forecast_archive.py
if ($LASTEXITCODE -ne 0) { throw "Forecast archive validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_feature_manifest.py
if ($LASTEXITCODE -ne 0) { throw "Feature manifest validation failed with exit code $LASTEXITCODE" }
