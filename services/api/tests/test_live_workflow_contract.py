from pathlib import Path


WORKFLOW = Path(__file__).parents[3] / ".github" / "workflows" / "live-provider-ingestion.yml"


def test_live_scheduler_fails_closed_on_ingestion_http_errors() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "set -euo pipefail" in workflow
    assert "curl --fail-with-body --silent --show-error" in workflow
    assert 'POST "$INGESTION_URL/internal/live-enrichment/run"' in workflow
    assert "--data \"$BODY\"" in workflow
    assert "NEXUS_INGESTION_TRIGGER_TOKEN" in workflow
