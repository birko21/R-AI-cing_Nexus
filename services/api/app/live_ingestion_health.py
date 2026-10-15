"""Safe operational health and coverage view for the licensed ingestion lane."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Literal
from uuid import uuid4

from sqlalchemy import Connection, Engine, text

from app.contracts import LiveIngestionCoverage, LiveIngestionStatus
from app.database_config import sqlalchemy_database_url
from app.runtime_config import RuntimeConfig


HealthStatus = Literal["DISABLED", "NO_DATA", "HEALTHY", "STALE", "FAILED"]


def _source_id(runtime: RuntimeConfig) -> str | None:
    if not runtime.live_provider or not runtime.live_operations:
        return None
    return f"{runtime.live_provider}:{runtime.live_operations[0]}"


def freshness_threshold_seconds() -> int:
    raw = os.environ.get("NEXUS_LIVE_FRESHNESS_MINUTES", "180").strip()
    try:
        minutes = int(raw)
    except ValueError as exc:
        raise RuntimeError("NEXUS_LIVE_FRESHNESS_MINUTES must be an integer") from exc
    if not 1 <= minutes <= 1440:
        raise RuntimeError("NEXUS_LIVE_FRESHNESS_MINUTES must be between 1 and 1440")
    return minutes * 60


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _age_seconds(now: datetime, value: datetime | None) -> int | None:
    if value is None:
        return None
    return max(0, int((now - value).total_seconds()))


def record_ingestion_health(
    connection: Connection,
    *,
    source_id: str,
    checked_at: datetime,
    success: bool,
) -> None:
    """Append a fixed-detail health event without storing provider errors or payloads."""

    connection.execute(
        text(
            """
            INSERT INTO source_health_events (
                event_id, source_id, checked_at, status, signal_kind, severity,
                detail, capabilities_disabled
            ) VALUES (
                :event_id, :source_id, :checked_at, :status, :signal_kind,
                :severity, :detail, FALSE
            )
            """
        ),
        {
            "event_id": f"health:{uuid4()}",
            "source_id": source_id,
            "checked_at": checked_at,
            "status": "HEALTHY" if success else "DEGRADED",
            "signal_kind": None if success else "OUTAGE",
            "severity": None if success else "CRITICAL",
            "detail": "bounded licensed ingestion completed" if success else "bounded licensed ingestion attempt failed",
        },
    )


def _base_status(runtime: RuntimeConfig, threshold: int) -> LiveIngestionStatus:
    if not runtime.live_enabled:
        return LiveIngestionStatus(status="DISABLED")
    return LiveIngestionStatus(
        status="NO_DATA",
        provider=runtime.live_provider,
        operation=runtime.live_operations[0] if runtime.live_operations else None,
        code=runtime.live_codes[0] if runtime.live_codes else None,
        freshness_threshold_seconds=threshold,
    )


def _status_from_rows(
    runtime: RuntimeConfig,
    *,
    now: datetime,
    threshold: int,
    latest_attempt: dict[str, object] | None,
    latest_success: dict[str, object] | None,
    latest_receipt: dict[str, object] | None,
    coverage: dict[str, object],
) -> LiveIngestionStatus:
    base = _base_status(runtime, threshold)
    success_at = _utc((latest_success or latest_receipt or {}).get("checked_at") or (latest_receipt or {}).get("created_at"))
    attempt_at = _utc((latest_attempt or {}).get("checked_at")) or success_at
    provider_response_at = _utc((latest_receipt or {}).get("retrieved_at"))
    response_age = _age_seconds(now, provider_response_at)
    failure = latest_attempt is not None and latest_attempt.get("status") != "HEALTHY"
    if failure:
        status: HealthStatus = "FAILED"
        failure_code: Literal["INGESTION_FAILED", "DATABASE_UNAVAILABLE"] | None = "INGESTION_FAILED"
    elif success_at is None:
        status = "NO_DATA"
        failure_code = None
    elif _age_seconds(now, success_at) is not None and _age_seconds(now, success_at) > threshold:
        status = "STALE"
        failure_code = None
    else:
        status = "HEALTHY"
        failure_code = None
    return LiveIngestionStatus(
        status=status,
        provider=base.provider,
        operation=base.operation,
        code=base.code,
        last_success_at=success_at,
        last_attempt_at=attempt_at,
        provider_response_at=provider_response_at,
        response_age_seconds=response_age,
        freshness_threshold_seconds=threshold,
        coverage=LiveIngestionCoverage(**{key: int(value or 0) for key, value in coverage.items()}),
        failure_code=failure_code,
    )


def read_live_ingestion_status(runtime: RuntimeConfig) -> LiveIngestionStatus:
    """Read only aggregate telemetry from Neon; never returns raw provider data."""

    threshold = freshness_threshold_seconds()
    if not runtime.live_enabled or runtime.persistence != "postgres":
        return _base_status(runtime, threshold)
    database_url = os.environ.get("DATABASE_URL", "").strip()
    source_id = _source_id(runtime)
    if not database_url or not source_id:
        return _base_status(runtime, threshold).model_copy(update={"status": "FAILED", "failure_code": "DATABASE_UNAVAILABLE"})
    engine: Engine | None = None
    try:
        from sqlalchemy import create_engine

        engine = create_engine(sqlalchemy_database_url(database_url), pool_pre_ping=True, pool_size=1, max_overflow=0)
        with engine.connect() as connection:
            latest_attempt = connection.execute(
                text(
                    """
                    SELECT status, checked_at
                    FROM source_health_events
                    WHERE source_id = :source_id
                    ORDER BY checked_at DESC, event_id DESC
                    LIMIT 1
                    """
                ),
                {"source_id": source_id},
            ).mappings().first()
            latest_success = connection.execute(
                text(
                    """
                    SELECT checked_at
                    FROM source_health_events
                    WHERE source_id = :source_id AND status = 'HEALTHY'
                    ORDER BY checked_at DESC, event_id DESC
                    LIMIT 1
                    """
                ),
                {"source_id": source_id},
            ).mappings().first()
            latest_receipt = connection.execute(
                text(
                    """
                    SELECT sr.source_receipt_id, sr.created_at, re.retrieved_at
                    FROM source_receipts sr
                    LEFT JOIN raw_envelopes re ON re.envelope_id = replace(sr.source_receipt_id, 'receipt:', '')
                    WHERE sr.source_identifier = :source_id
                      AND sr.data_mode = 'LICENSED'
                      AND sr.rights_state = 'APPROVED'
                    ORDER BY COALESCE(re.retrieved_at, sr.created_at) DESC, sr.source_receipt_id DESC
                    LIMIT 1
                    """
                ),
                {"source_id": source_id},
            ).mappings().first()
            coverage = connection.execute(
                text(
                    """
                    SELECT
                        (SELECT count(DISTINCT m.meeting_id)
                           FROM meetings m JOIN source_receipts sr ON sr.source_receipt_id = m.source_receipt_id
                          WHERE sr.source_identifier = :source_id AND m.data_mode = 'LICENSED') AS meetings,
                        (SELECT count(DISTINCT rr.race_id)
                           FROM race_revisions rr JOIN source_receipts sr ON sr.source_receipt_id = rr.source_receipt_id
                          WHERE sr.source_identifier = :source_id AND rr.data_mode = 'LICENSED') AS races,
                        (SELECT count(DISTINCT er.entry_id)
                           FROM entry_revisions er JOIN source_receipts sr ON sr.source_receipt_id = er.source_receipt_id
                          WHERE sr.source_identifier = :source_id AND er.data_mode = 'LICENSED') AS entries,
                        (SELECT count(DISTINCT orr.result_id)
                           FROM official_result_revisions orr JOIN source_receipts sr ON sr.source_receipt_id = orr.source_receipt_id
                          WHERE sr.source_identifier = :source_id AND orr.data_mode = 'LICENSED') AS results
                    """
                ),
                {"source_id": source_id},
            ).mappings().one()
            now = datetime.now(timezone.utc)
            receipt_row = dict(latest_receipt) if latest_receipt is not None else None
            if receipt_row is not None:
                receipt_row["checked_at"] = receipt_row.get("created_at")
            return _status_from_rows(
                runtime,
                now=now,
                threshold=threshold,
                latest_attempt=dict(latest_attempt) if latest_attempt is not None else None,
                latest_success=dict(latest_success) if latest_success is not None else None,
                latest_receipt=receipt_row,
                coverage=dict(coverage),
            )
    except Exception:
        return _base_status(runtime, threshold).model_copy(update={"status": "FAILED", "failure_code": "DATABASE_UNAVAILABLE"})
    finally:
        if engine is not None:
            engine.dispose()
