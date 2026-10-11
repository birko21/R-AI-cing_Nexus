param()

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Run pnpm bootstrap before database smoke.' }

& '.venv\Scripts\python.exe' scripts/validate_database_target.py
if ($LASTEXITCODE -ne 0) { throw "Database target validation failed with exit code $LASTEXITCODE" }

& '.venv\Scripts\python.exe' -m alembic -c alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) { throw "Alembic upgrade failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/record_migration_checksums.py
if ($LASTEXITCODE -ne 0) { throw "Migration checksum recording failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/verify_migration_checksums.py
if ($LASTEXITCODE -ne 0) { throw "Migration checksum verification failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/verify_ingestion_schema.py
if ($LASTEXITCODE -ne 0) { throw "Ingestion schema verification failed with exit code $LASTEXITCODE" }

& '.venv\Scripts\python.exe' -m alembic -c alembic.ini downgrade base
if ($LASTEXITCODE -ne 0) { throw "Alembic downgrade failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' -m alembic -c alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) { throw "Alembic re-upgrade failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/record_migration_checksums.py
if ($LASTEXITCODE -ne 0) { throw "Final migration checksum recording failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/verify_migration_checksums.py
if ($LASTEXITCODE -ne 0) { throw "Final migration checksum verification failed with exit code $LASTEXITCODE" }
& '.venv\Scripts\python.exe' scripts/verify_ingestion_schema.py
if ($LASTEXITCODE -ne 0) { throw "Final ingestion schema verification failed with exit code $LASTEXITCODE" }

Write-Output 'POSTGRES SMOKE COMPLETE: upgrade/checksum/schema/downgrade/re-upgrade'
