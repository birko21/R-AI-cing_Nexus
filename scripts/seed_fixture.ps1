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
& '.venv\Scripts\python.exe' scripts/generate_split_manifest.py
if ($LASTEXITCODE -ne 0) { throw "Split manifest validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_metric_report.py
if ($LASTEXITCODE -ne 0) { throw "Metric report validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_diagnostics_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Diagnostics fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_registry_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Registry fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_scraping_policy_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Scraping policy fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_provider_capability_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Provider capability fixture validation failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/generate_scraped_provenance_fixture.py
if ($LASTEXITCODE -ne 0) { throw "Scraped provenance fixture validation failed with exit code $LASTEXITCODE" }
