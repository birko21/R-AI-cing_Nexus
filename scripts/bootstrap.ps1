$ErrorActionPreference = 'Stop'

Write-Output 'Checking local development prerequisites...'

if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js is required.' }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python 3.11+ is required.' }
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) { throw 'pnpm is required.' }

$pythonVersion = [version]((python --version) -replace 'Python ', '')
if ($pythonVersion.Major -lt 3 -or ($pythonVersion.Major -eq 3 -and $pythonVersion.Minor -lt 11)) {
    throw "Python 3.11+ required; found $pythonVersion"
}

$pgReady = 'C:\Program Files\PostgreSQL\18\bin\pg_isready.exe'
if (Test-Path -LiteralPath $pgReady) {
    & $pgReady -h 127.0.0.1 -p 5432
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL is installed but not accepting local connections.' }
} else {
    Write-Warning 'PostgreSQL 18 pg_isready.exe was not found at the standard path. Install PostgreSQL or set an equivalent local prerequisite before G1.'
}

if (-not (Test-Path -LiteralPath '.venv')) {
    python -m venv .venv
}

& '.venv\Scripts\python.exe' -m pip install --disable-pip-version-check --upgrade pip | Out-Host
& '.venv\Scripts\python.exe' -m pip install --disable-pip-version-check -e 'services/api[dev]' | Out-Host
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }

pnpm install --no-frozen-lockfile
if ($LASTEXITCODE -ne 0) { throw 'Node dependency installation failed.' }

Write-Output 'BOOTSTRAP READY'
