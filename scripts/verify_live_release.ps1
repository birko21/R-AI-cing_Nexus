[CmdletBinding()]
param(
    [string]$ApiBaseUrl = "https://nexus-staging-api-feap.onrender.com",
    [string]$FrontendUrl = "https://nexus-staging-frontend.onrender.com"
)

$ErrorActionPreference = "Stop"

$status = Invoke-RestMethod -UseBasicParsing "$ApiBaseUrl/v1/system/status"
$unauthenticatedMeetings = Invoke-WebRequest -UseBasicParsing -SkipHttpErrorCheck "$ApiBaseUrl/v1/meetings"
$verificationQuery = [DateTime]::UtcNow.ToString("yyyyMMddHHmmss")
$frontendPage = Invoke-WebRequest -UseBasicParsing "$FrontendUrl/?live_release_verify=$verificationQuery"
$assetMatch = [regex]::Match($frontendPage.Content, 'src="([^"]+\.js)"')
if (-not $assetMatch.Success) {
    throw "frontend JavaScript asset was not found"
}
$frontendBundle = Invoke-WebRequest -UseBasicParsing "$FrontendUrl$($assetMatch.Groups[1].Value)?live_release_verify=$verificationQuery"

$safeChecks = @{
    api_status = $status.data_mode -eq "LICENSED" -and $status.persistence -eq "postgres"
    ingestion_status = $status.live_ingestion.status -eq "HEALTHY"
    ingestion_coverage = $status.live_ingestion.coverage.meetings -gt 0 -and $status.live_ingestion.coverage.entries -gt 0
    wagering_disabled = $status.wagering_enabled -eq $false
    protected_meetings = $unauthenticatedMeetings.StatusCode -eq 401
    frontend_page = $frontendPage.StatusCode -eq 200
    frontend_bundle = $frontendBundle.StatusCode -eq 200 -and $frontendBundle.Content -match "LICENSED INGESTION MONITOR"
    no_status_payload = -not ($status.PSObject.Properties.Name -contains "payload")
}

if ($safeChecks.Values -contains $false) {
    $safeChecks.GetEnumerator() | Sort-Object Name | Format-Table -AutoSize
    throw "live release verification failed"
}

[pscustomobject]@{
    RESULT = "PASS"
    DATA_MODE = $status.data_mode
    PERSISTENCE = $status.persistence
    INGESTION_STATUS = $status.live_ingestion.status
    PROVIDER = $status.live_ingestion.provider
    OPERATION = $status.live_ingestion.operation
    MEETINGS = $status.live_ingestion.coverage.meetings
    RACES = $status.live_ingestion.coverage.races
    ENTRIES = $status.live_ingestion.coverage.entries
    RESULTS = $status.live_ingestion.coverage.results
    WAGERING_ENABLED = $status.wagering_enabled
    PROTECTED_MEETINGS_HTTP = $unauthenticatedMeetings.StatusCode
    FRONTEND_HTTP = $frontendPage.StatusCode
    FRONTEND_MONITOR = "present"
    RAW_STATUS_PAYLOAD = "absent"
} | Format-List
