from datetime import datetime, timedelta, timezone

from app.live_ingestion_health import _status_from_rows
from app.runtime_config import load_runtime_config


NOW = datetime(2026, 10, 15, 1, 0, tzinfo=timezone.utc)


def runtime():
    return load_runtime_config(
        environ={
            "APP_ENV": "staging",
            "NEXUS_DATA_MODE": "LICENSED",
            "NEXUS_API_PERSISTENCE": "postgres",
            "NEXUS_LIVE_PROVIDER": "punters-edge",
            "NEXUS_LIVE_OPERATIONS": "GET_RESULTS",
            "NEXUS_LIVE_CODES": "THOROUGHBRED",
            "NEXUS_LIVE_READ_ONLY": "true",
        }
    )


def receipt(at: datetime) -> dict[str, object]:
    return {"created_at": at, "retrieved_at": at, "checked_at": at}


def coverage() -> dict[str, int]:
    return {"meetings": 1, "races": 1, "entries": 12, "results": 1}


def test_live_ingestion_health_reports_fresh_success_and_coverage() -> None:
    checked_at = NOW - timedelta(minutes=12)
    status = _status_from_rows(
        runtime(),
        now=NOW,
        threshold=180 * 60,
        latest_attempt={"status": "HEALTHY", "checked_at": checked_at},
        latest_success={"checked_at": checked_at},
        latest_receipt=receipt(checked_at),
        coverage=coverage(),
    )

    assert status.status == "HEALTHY"
    assert status.response_age_seconds == 12 * 60
    assert status.coverage.entries == 12
    assert status.failure_code is None


def test_live_ingestion_health_reports_stale_success() -> None:
    checked_at = NOW - timedelta(hours=4)
    status = _status_from_rows(
        runtime(),
        now=NOW,
        threshold=180 * 60,
        latest_attempt={"status": "HEALTHY", "checked_at": checked_at},
        latest_success={"checked_at": checked_at},
        latest_receipt=receipt(checked_at),
        coverage=coverage(),
    )

    assert status.status == "STALE"
    assert status.coverage.races == 1


def test_live_ingestion_health_reports_latest_failure_without_error_text() -> None:
    success_at = NOW - timedelta(minutes=20)
    failure_at = NOW - timedelta(minutes=2)
    status = _status_from_rows(
        runtime(),
        now=NOW,
        threshold=180 * 60,
        latest_attempt={"status": "DEGRADED", "checked_at": failure_at},
        latest_success={"checked_at": success_at},
        latest_receipt=receipt(success_at),
        coverage=coverage(),
    )

    assert status.status == "FAILED"
    assert status.last_success_at == success_at
    assert status.last_attempt_at == failure_at
    assert status.failure_code == "INGESTION_FAILED"
    assert "error" not in status.model_dump()
