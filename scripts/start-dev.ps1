$ErrorActionPreference = 'Stop'

if (Test-Path -LiteralPath '.env.local') {
    foreach ($line in Get-Content -LiteralPath '.env.local') {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith('#')) { continue }
        $separator = $line.IndexOf('=')
        if ($separator -le 0) { continue }
        $key = $line.Substring(0, $separator).Trim()
        $value = $line.Substring($separator + 1)
        if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        Set-Item -Path ("Env:" + $key) -Value $value
    }
}

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
