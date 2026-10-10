param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw "Checkpoint not found: $Path"
}

$checkpoint = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
$required = @(
    'gate', 'title', 'status', 'completed', 'commands', 'security',
    'data_mode', 'data_rights', 'model_status', 'evidence', 'cost',
    'risks', 'owner_decisions', 'next_unblocked_gate'
)

foreach ($field in $required) {
    if ($null -eq $checkpoint.$field) {
        throw "Missing required checkpoint field: $field"
    }
}

if ($checkpoint.status -notin @('PASS', 'CONDITIONAL_PASS', 'BLOCKED', 'FAIL')) {
    throw "Invalid checkpoint status: $($checkpoint.status)"
}

if ($checkpoint.commands.Count -eq 0) {
    throw 'Checkpoint must contain at least one observed command.'
}

foreach ($command in $checkpoint.commands) {
    if ($null -eq $command.command -or $null -eq $command.exit_code -or $null -eq $command.observed_at_utc) {
        throw 'Every command requires command, exit_code and observed_at_utc.'
    }
}

if ($checkpoint.status -in @('PASS', 'CONDITIONAL_PASS') -and @($checkpoint.risks).Count -gt 0) {
    Write-Warning 'Checkpoint has recorded risks; confirm none are hard blockers before treating it as releasable.'
}

Write-Output "VALID CHECKPOINT: $($checkpoint.gate) / $($checkpoint.status)"
