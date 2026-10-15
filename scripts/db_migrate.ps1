param(
    [ValidateSet('upgrade', 'downgrade')]
    [string]$Direction = 'upgrade'
)

$ErrorActionPreference = 'Stop'

if (-not $env:DATABASE_URL) { throw 'DATABASE_URL must be set to a disposable local PostgreSQL database.' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Run pnpm bootstrap before database migrations.' }

& '.venv\Scripts\python.exe' scripts/validate_database_target.py
if ($LASTEXITCODE -ne 0) { throw "Database target validation failed with exit code $LASTEXITCODE" }

if ($Direction -eq 'upgrade') {
    & '.venv\Scripts\python.exe' -m alembic -c alembic.ini upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Alembic upgrade failed with exit code $LASTEXITCODE" }
    & '.venv\Scripts\python.exe' scripts/record_migration_checksums.py
    if ($LASTEXITCODE -ne 0) { throw "Migration checksum recording failed with exit code $LASTEXITCODE" }
    & '.venv\Scripts\python.exe' scripts/verify_migration_checksums.py
    if ($LASTEXITCODE -ne 0) { throw "Migration checksum verification failed with exit code $LASTEXITCODE" }
} else {
    & '.venv\Scripts\python.exe' -m alembic -c alembic.ini downgrade base
    if ($LASTEXITCODE -ne 0) { throw "Alembic downgrade failed with exit code $LASTEXITCODE" }
    Write-Output 'MIGRATION DOWNGRADE COMPLETE: base'
}
