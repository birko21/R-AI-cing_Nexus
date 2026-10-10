$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    powershell -ExecutionPolicy Bypass -File 'scripts/bootstrap.ps1'
}

$api = Start-Process -FilePath '.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','app.main:app','--app-dir','services/api','--host','127.0.0.1','--port','8000' -PassThru
try {
    pnpm --filter @racing-intelligence/web dev --host 127.0.0.1
}
finally {
    if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id }
}
