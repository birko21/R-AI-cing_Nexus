$ErrorActionPreference = 'Stop'

$manifestPath = 'fixtures/synthetic/manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Synthetic fixture manifest not found: $manifestPath"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.data_mode -ne 'SYNTHETIC_ONLY' -or $manifest.fictional -ne $true) {
    throw 'Fixture manifest must remain explicitly synthetic and fictional.'
}

Write-Output "FIXTURE READY: $($manifest.fixture_id) / mode=$($manifest.data_mode) / seed=$($manifest.seed)"
Write-Output 'Full three-code fixture generation is scheduled for RIL-016.'
