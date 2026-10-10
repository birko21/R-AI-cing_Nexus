$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Run pnpm bootstrap before seeding fixtures.' }
& '.venv\Scripts\python.exe' scripts/generate_synthetic_fixtures.py --check
if ($LASTEXITCODE -ne 0) { throw "Synthetic fixture validation failed with exit code $LASTEXITCODE" }
