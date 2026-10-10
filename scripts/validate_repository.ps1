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
    'fixtures/synthetic/fixture.json',
    'fixtures/synthetic/forecasts_b0.json',
    'fixtures/synthetic/forecasts_b1.json',
    'playwright.config.ts',
    'e2e/command-centre.spec.ts',
    'contracts/openapi_mvp.yaml',
    'contracts/types.ts',
    'services/api/app/contracts.py',
    'services/api/app/auth.py',
    'services/api/app/pagination.py',
    'services/api/app/domain.py',
    'services/api/app/lifecycle.py',
    'services/api/app/temporal.py',
    'services/api/app/provenance.py',
    'services/api/app/capabilities.py',
    'services/api/app/baseline.py',
    'services/api/app/form_heuristic.py',
    'services/api/app/probability.py',
    'services/api/tests/test_contract.py',
    'services/api/tests/test_api.py',
    'services/api/tests/test_domain.py',
    'services/api/tests/test_lifecycle.py',
    'services/api/tests/test_temporal.py',
    'services/api/tests/test_provenance.py',
    'services/api/tests/test_capabilities.py',
    'services/api/tests/test_fixtures.py',
    'services/api/tests/test_baseline.py',
    'services/api/tests/test_form_heuristic.py',
    'services/api/tests/test_probability.py',
    'docs/domain/ENTITY_DICTIONARY.md',
    'docs/domain/RACE_LIFECYCLE.md',
    'docs/domain/BITEMPORAL_QUERIES.md',
    'docs/domain/RAW_ENVELOPES.md',
    'docs/domain/RIGHTS_MATRIX.md',
    'docs/evidence/ril-017/command-centre-desktop.png',
    'docs/evidence/ril-017/command-centre-mobile.png',
    'docs/evidence/ril-018/race-research-view.png',
    'docs/evidence/ril-019/thoroughbred-panel.png',
    'docs/evidence/ril-019/harness-panel.png',
    'docs/evidence/ril-019/greyhound-panel.png',
    'docs/evidence/ril-020/accessibility-report.md',
    'docs/evidence/ril-020/degraded-desktop.png',
    'docs/evidence/ril-020/degraded-mobile.png',
    'docs/evidence/ril-023/probability-edge-cases.md',
    'docs/models/B0_UNIFORM_BASELINE.md',
    'docs/models/B1_FORM_HEURISTIC.md',
    'docs/models/PROBABILITY_VALIDATION.md',
    'alembic.ini',
    'migrations/env.py',
    'migrations/versions/001_offline_mvp.py',
    'migrations/versions/002_domain_mappings.py',
    'migrations/versions/003_race_lifecycle_events.py',
    'migrations/versions/004_bitemporal_revisions.py',
    'migrations/versions/005_raw_envelopes_quarantine.py',
    'migrations/versions/006_capability_controls.py',
    'scripts/db_migrate.ps1',
    'scripts/generate_synthetic_fixtures.py',
    'scripts/generate_b0_forecast_manifest.py',
    'scripts/generate_b1_forecast_manifest.py',
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
