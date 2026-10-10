$ErrorActionPreference = 'Stop'

Write-Output 'Checking repository whitespace...'
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check failed with exit code $LASTEXITCODE"
}

$required = @(
    'README.md',
    'README_START_HERE.md',
    'docs/product/MASTER_SPEC_V1_1.md',
    'docs/product/CODEX_EXECUTION_PROMPT_V1_1.md',
    'docs/product/SOURCE_MANIFEST.md',
    'docs/DECISION_REGISTER.md',
    'docs/TRACEABILITY.md',
    'docs/RISK_REGISTER.md',
    'docs/WORKFLOW.md',
    'docs/checkpoints/checkpoint.schema.json',
    'scripts/validate_checkpoint.ps1'
)

foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required repository baseline file is missing: $path"
    }
}

Get-Content -LiteralPath 'docs/checkpoints/checkpoint.schema.json' -Raw | ConvertFrom-Json | Out-Null
powershell -ExecutionPolicy Bypass -File 'scripts/validate_checkpoint.ps1' -Path 'docs/checkpoints/examples/GATE_G0_BLOCKED.json'
if ($LASTEXITCODE -ne 0) {
    throw "Checkpoint validation failed with exit code $LASTEXITCODE"
}

Write-Output "REPOSITORY BASELINE VALID: $($required.Count) required files present"
