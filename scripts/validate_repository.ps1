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
    'docs/LOCAL_DEVELOPMENT.md',
    'docs/checkpoints/checkpoint.schema.json',
    'scripts/validate_checkpoint.ps1',
    '.env.example',
    'package.json',
    'pnpm-workspace.yaml',
    'pnpm-lock.yaml',
    'apps/web/package.json',
    'services/api/pyproject.toml',
    'services/api/requirements.lock.txt',
    'fixtures/synthetic/manifest.json',
    'contracts/openapi_mvp.yaml',
    'contracts/types.ts',
    'services/api/app/contracts.py',
    'services/api/app/auth.py',
    'services/api/app/pagination.py',
    'services/api/tests/test_contract.py',
    'services/api/tests/test_api.py',
    'alembic.ini',
    'migrations/env.py',
    'migrations/versions/001_offline_mvp.py',
    'scripts/db_migrate.ps1',
    'scripts/record_migration_checksums.py',
    'scripts/verify_migration_checksums.py'
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
