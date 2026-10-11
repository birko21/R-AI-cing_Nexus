"""Synthetic-only ingestion worker primitives.

The active MVP does not require a broker or a cloud worker.  This module keeps
the processing contract provider-neutral while making the important job
semantics executable locally: bounded pages, retries, idempotency, append-only
raw envelopes, quarantine, and deterministic pagination continuation.

The in-memory store is deliberately an offline reference store.  A later
PostgreSQL repository can implement the same operations against the existing
``raw_envelopes`` and ``quarantine_records`` tables without changing the
worker's provider boundary.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import json
from typing import Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.provenance import QuarantineRecord, RawEnvelope, ingest_raw_envelope
from app.providers import ContractedProviderAdapter, ProviderOperation


JobStatus = Literal["QUEUED", "RUNNING", "SUCCEEDED", "RETRYABLE", "FAILED", "QUARANTINED", "SKIPPED"]
RecordDisposition = Literal["PERSISTED", "DUPLICATE", "QUARANTINED"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IngestionJob(BaseModel):
    """Serializable unit of bounded provider work."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    job_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    idempotency_key: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    operation: ProviderOperation
    code: str = Field(min_length=1)
    cursor: str | None = None
    replay_id: str = Field(default="default", min_length=1)
    page_size: int = Field(default=100, ge=1, le=100)
    attempt: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1, le=10)
    status: JobStatus = "QUEUED"
    available_at: datetime = Field(default_factory=_utc_now)
    lease_owner: str | None = None
    lease_until: datetime | None = None
    records_persisted: int = Field(default=0, ge=0)
    records_skipped: int = Field(default=0, ge=0)
    records_quarantined: int = Field(default=0, ge=0)
    error: str | None = None
    created_at: datetime = Field(default_factory=_utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    continuation_job_id: str | None = None

    @model_validator(mode="after")
    def validate_timestamps(self) -> IngestionJob:
        for field_name in ("available_at", "created_at", "started_at", "finished_at", "lease_until"):
            value = getattr(self, field_name)
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError(f"{field_name} must be timezone-aware")
        if self.attempt >= self.max_attempts and self.status == "RETRYABLE":
            raise ValueError("a job at its attempt limit cannot remain retryable")
        return self


class IngestionRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    jobs_processed: int = Field(default=0, ge=0)
    jobs_succeeded: int = Field(default=0, ge=0)
    jobs_failed: int = Field(default=0, ge=0)
    jobs_quarantined: int = Field(default=0, ge=0)
    envelopes_persisted: int = Field(default=0, ge=0)
    envelopes_skipped: int = Field(default=0, ge=0)
    records_quarantined: int = Field(default=0, ge=0)


class IngestionStore(Protocol):
    def enqueue_job(self, job: IngestionJob) -> IngestionJob: ...

    def has_pending(self) -> bool: ...

    def claim_next(self, worker_id: str, *, lease_seconds: int, now: datetime) -> IngestionJob | None: ...

    def append_envelope(self, envelope: RawEnvelope) -> RecordDisposition: ...

    def append_quarantine(self, record: QuarantineRecord) -> None: ...

    def mark_succeeded(
        self,
        job_id: str,
        *,
        records_persisted: int,
        records_skipped: int,
        records_quarantined: int,
        continuation_job_id: str | None = None,
        finished_at: datetime | None = None,
    ) -> IngestionJob: ...

    def mark_retryable(self, job_id: str, *, error: str, available_at: datetime) -> IngestionJob: ...

    def mark_failed(self, job_id: str, *, error: str, finished_at: datetime | None = None) -> IngestionJob: ...


class InMemoryIngestionStore:
    """Append-only offline store and queue state for deterministic worker runs."""

    def __init__(self) -> None:
        self.jobs: dict[str, IngestionJob] = {}
        self.raw_envelopes: dict[str, RawEnvelope] = {}
        self.quarantine_records: dict[str, QuarantineRecord] = {}
        self._idempotency_index: dict[str, str] = {}
        self._queued_job_ids: deque[str] = deque()

    def create_job(self, job: IngestionJob) -> tuple[IngestionJob, bool]:
        """Create a job once; return ``(job, created)`` for idempotent enqueue."""

        existing_id = self._idempotency_index.get(job.idempotency_key)
        if existing_id is not None:
            return self.jobs[existing_id], False
        self.jobs[job.job_id] = job
        self._idempotency_index[job.idempotency_key] = job.job_id
        self._queued_job_ids.append(job.job_id)
        return job, True

    def enqueue_job(self, job: IngestionJob) -> IngestionJob:
        return self.create_job(job)[0]

    def next_queued(self) -> IngestionJob | None:
        while self._queued_job_ids:
            job_id = self._queued_job_ids.popleft()
            job = self.jobs[job_id]
            if job.status == "QUEUED":
                return job
        return None

    def has_pending(self) -> bool:
        return any(self.jobs[job_id].status == "QUEUED" for job_id in self._queued_job_ids)

    def claim_next(self, worker_id: str, *, lease_seconds: int, now: datetime) -> IngestionJob | None:
        job = self.next_queued()
        if job is None:
            return None
        return self.update_job(
            job.job_id,
            status="RUNNING",
            attempt=job.attempt + 1,
            lease_owner=worker_id,
            lease_until=now + timedelta(seconds=lease_seconds),
            started_at=job.started_at or now,
            error=None,
        )

    def update_job(self, job_id: str, **changes: object) -> IngestionJob:
        current = self.jobs[job_id]
        updated = current.model_copy(update=changes)
        self.jobs[job_id] = updated
        if updated.status == "QUEUED":
            self._queued_job_ids.append(job_id)
        return updated

    def append_quarantine(self, record: QuarantineRecord) -> None:
        self.quarantine_records[record.quarantine_id] = record

    def append_envelope(self, envelope: RawEnvelope) -> RecordDisposition:
        existing = self.raw_envelopes.get(envelope.envelope_id)
        if existing is None:
            self.raw_envelopes[envelope.envelope_id] = envelope
            return "PERSISTED"
        if existing.payload_sha256 == envelope.payload_sha256:
            return "DUPLICATE"

        self.append_quarantine(
            QuarantineRecord(
                envelope_id=envelope.envelope_id,
                reason_code="UNRESOLVED_IDENTITY",
                detail="envelope_id was replayed with a different payload checksum",
            )
        )
        return "QUARANTINED"

    def mark_succeeded(
        self,
        job_id: str,
        *,
        records_persisted: int,
        records_skipped: int,
        records_quarantined: int,
        continuation_job_id: str | None = None,
        finished_at: datetime | None = None,
    ) -> IngestionJob:
        return self.update_job(
            job_id,
            status="QUARANTINED" if records_quarantined else "SUCCEEDED",
            records_persisted=records_persisted,
            records_skipped=records_skipped,
            records_quarantined=records_quarantined,
            continuation_job_id=continuation_job_id,
            finished_at=finished_at or _utc_now(),
            lease_owner=None,
            lease_until=None,
        )

    def mark_retryable(self, job_id: str, *, error: str, available_at: datetime) -> IngestionJob:
        return self.update_job(
            job_id,
            status="QUEUED",
            error=error,
            available_at=available_at,
            lease_owner=None,
            lease_until=None,
        )

    def mark_failed(self, job_id: str, *, error: str, finished_at: datetime | None = None) -> IngestionJob:
        return self.update_job(
            job_id,
            status="FAILED",
            error=error,
            finished_at=finished_at or _utc_now(),
            lease_owner=None,
            lease_until=None,
        )


class PostgresIngestionStore:
    """PostgreSQL repository for jobs and raw receipts.

    The caller owns the SQLAlchemy transaction and connection lifecycle. This
    keeps the repository usable from a local command, an API task, or a future
    scheduler without making the worker responsible for process management.
    """

    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def enqueue_job(self, job: IngestionJob) -> IngestionJob:
        self.connection.execute(
            text(
                """
                INSERT INTO ingestion_jobs (
                    job_id, idempotency_key, provider_id, operation, code, cursor,
                    replay_id, page_size, attempt, max_attempts, status, available_at,
                    lease_owner, lease_until,
                    records_persisted, records_skipped, records_quarantined,
                    error, created_at, started_at, finished_at, continuation_job_id
                ) VALUES (
                    :job_id, :idempotency_key, :provider_id, :operation, :code, :cursor,
                    :replay_id, :page_size, :attempt, :max_attempts, :status, :available_at,
                    :lease_owner, :lease_until,
                    :records_persisted, :records_skipped, :records_quarantined,
                    :error, :created_at, :started_at, :finished_at, :continuation_job_id
                ) ON CONFLICT (idempotency_key) DO NOTHING
                """
            ),
            self._job_params(job),
        )
        row = self.connection.execute(
            text("SELECT * FROM ingestion_jobs WHERE idempotency_key = :idempotency_key"),
            {"idempotency_key": job.idempotency_key},
        ).mappings().one()
        return self._job_from_row(row)

    def has_pending(self) -> bool:
        return bool(
            self.connection.execute(
                text(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM ingestion_jobs
                        WHERE status IN ('QUEUED', 'RETRYABLE')
                           OR (status = 'RUNNING' AND lease_until < now())
                    )
                    """
                )
            ).scalar_one()
        )

    def claim_next(self, worker_id: str, *, lease_seconds: int = 60, now: datetime | None = None) -> IngestionJob | None:
        if not worker_id.strip():
            raise ValueError("worker_id is required")
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        claimed_at = (now or _utc_now()).astimezone(timezone.utc)
        lease_until = claimed_at + timedelta(seconds=lease_seconds)
        self.recover_expired_leases(now=claimed_at)
        row = self.connection.execute(
            text(
                """
                WITH candidate AS (
                    SELECT job_id
                    FROM ingestion_jobs
                    WHERE (
                        status IN ('QUEUED', 'RETRYABLE')
                        AND available_at <= :claimed_at
                        AND attempt < max_attempts
                    ) OR (
                        status = 'RUNNING'
                        AND lease_until < :claimed_at
                        AND attempt < max_attempts
                    )
                    ORDER BY available_at, created_at, job_id
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE ingestion_jobs AS job
                SET status = 'RUNNING',
                    lease_owner = :worker_id,
                    lease_until = :lease_until,
                    started_at = COALESCE(job.started_at, :claimed_at),
                    attempt = job.attempt + 1,
                    error = NULL
                FROM candidate
                WHERE job.job_id = candidate.job_id
                RETURNING job.*
                """
            ),
            {"claimed_at": claimed_at, "lease_until": lease_until, "worker_id": worker_id},
        ).mappings().first()
        return self._job_from_row(row) if row is not None else None

    def recover_expired_leases(self, *, now: datetime | None = None) -> int:
        """Move expired work back to retryable or terminal failure state."""

        recovered_at = (now or _utc_now()).astimezone(timezone.utc)
        result = self.connection.execute(
            text(
                """
                UPDATE ingestion_jobs
                SET status = CASE WHEN attempt < max_attempts THEN 'RETRYABLE' ELSE 'FAILED' END,
                    available_at = :recovered_at,
                    finished_at = CASE WHEN attempt < max_attempts THEN NULL ELSE :recovered_at END,
                    error = CASE WHEN attempt < max_attempts THEN 'lease expired; job returned to queue' ELSE 'lease expired at attempt limit' END,
                    lease_owner = NULL,
                    lease_until = NULL
                WHERE status = 'RUNNING' AND lease_until < :recovered_at
                """
            ),
            {"recovered_at": recovered_at},
        )
        return result.rowcount

    def mark_succeeded(
        self,
        job_id: str,
        *,
        records_persisted: int,
        records_skipped: int,
        records_quarantined: int,
        continuation_job_id: str | None = None,
        finished_at: datetime | None = None,
    ) -> IngestionJob:
        return self._update_job(
            job_id,
            status="QUARANTINED" if records_quarantined else "SUCCEEDED",
            records_persisted=records_persisted,
            records_skipped=records_skipped,
            records_quarantined=records_quarantined,
            continuation_job_id=continuation_job_id,
            finished_at=finished_at or _utc_now(),
            lease_owner=None,
            lease_until=None,
        )

    def mark_retryable(self, job_id: str, *, error: str, available_at: datetime) -> IngestionJob:
        return self._update_job(
            job_id,
            status="RETRYABLE",
            error=error,
            available_at=available_at,
            lease_owner=None,
            lease_until=None,
        )

    def mark_failed(self, job_id: str, *, error: str, finished_at: datetime | None = None) -> IngestionJob:
        return self._update_job(
            job_id,
            status="FAILED",
            error=error,
            finished_at=finished_at or _utc_now(),
            lease_owner=None,
            lease_until=None,
        )

    def append_envelope(self, envelope: RawEnvelope) -> RecordDisposition:
        result = self.connection.execute(
            text(
                """
                INSERT INTO raw_envelopes (
                    envelope_id, source_identifier, payload, payload_sha256, schema_version,
                    retrieved_at, first_observed_at, published_at, data_mode, rights_state,
                    licence_reference, retrieval_metadata
                ) VALUES (
                    :envelope_id, :source_identifier, CAST(:payload AS jsonb),
                    :payload_sha256, :schema_version,
                    :retrieved_at, :first_observed_at, :published_at, :data_mode, :rights_state,
                    :licence_reference, CAST(:retrieval_metadata AS jsonb)
                ) ON CONFLICT (envelope_id) DO NOTHING
                """
            ),
            {
                "envelope_id": envelope.envelope_id,
                "source_identifier": envelope.source_identifier,
                "payload": json.dumps(envelope.payload, ensure_ascii=False, separators=(",", ":")),
                "payload_sha256": envelope.payload_sha256,
                "schema_version": envelope.schema_version,
                "retrieved_at": envelope.retrieved_at,
                "first_observed_at": envelope.first_observed_at,
                "published_at": envelope.published_at,
                "data_mode": envelope.data_mode,
                "rights_state": envelope.rights_state,
                "licence_reference": envelope.licence_reference,
                "retrieval_metadata": json.dumps(envelope.retrieval_metadata, ensure_ascii=False, separators=(",", ":")),
            },
        )
        if result.rowcount == 1:
            return "PERSISTED"
        existing = self.connection.execute(
            text("SELECT payload_sha256 FROM raw_envelopes WHERE envelope_id = :envelope_id"),
            {"envelope_id": envelope.envelope_id},
        ).scalar_one()
        if existing == envelope.payload_sha256:
            return "DUPLICATE"
        self.append_quarantine(
            QuarantineRecord(
                envelope_id=envelope.envelope_id,
                reason_code="UNRESOLVED_IDENTITY",
                detail="envelope_id was replayed with a different payload checksum",
            )
        )
        return "QUARANTINED"

    def append_quarantine(self, record: QuarantineRecord) -> None:
        self.connection.execute(
            text(
                """
                INSERT INTO quarantine_records (quarantine_id, envelope_id, reason_code, detail, created_at)
                VALUES (:quarantine_id, :envelope_id, :reason_code, :detail, :created_at)
                """
            ),
            {
                "quarantine_id": record.quarantine_id,
                "envelope_id": record.envelope_id,
                "reason_code": record.reason_code,
                "detail": record.detail,
                "created_at": record.created_at,
            },
        )

    def _update_job(self, job_id: str, **changes: object) -> IngestionJob:
        allowed = {
            "status", "records_persisted", "records_skipped", "records_quarantined", "continuation_job_id",
            "error", "available_at", "finished_at", "lease_owner", "lease_until",
        }
        if not set(changes).issubset(allowed):
            raise ValueError("unsupported ingestion job update")
        assignments = ", ".join(f"{key} = :{key}" for key in changes)
        params = {"job_id": job_id, **changes}
        row = self.connection.execute(
            text(f"UPDATE ingestion_jobs SET {assignments} WHERE job_id = :job_id RETURNING *"),
            params,
        ).mappings().one()
        return self._job_from_row(row)

    @staticmethod
    def _job_params(job: IngestionJob) -> dict[str, object]:
        return {
            "job_id": job.job_id,
            "idempotency_key": job.idempotency_key,
            "provider_id": job.provider_id,
            "operation": job.operation,
            "code": job.code,
            "cursor": job.cursor,
            "replay_id": job.replay_id,
            "page_size": job.page_size,
            "attempt": job.attempt,
            "max_attempts": job.max_attempts,
            "status": job.status,
            "available_at": job.available_at,
            "lease_owner": job.lease_owner,
            "lease_until": job.lease_until,
            "records_persisted": job.records_persisted,
            "records_skipped": job.records_skipped,
            "records_quarantined": job.records_quarantined,
            "error": job.error,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "continuation_job_id": job.continuation_job_id,
        }

    @staticmethod
    def _job_from_row(row: object) -> IngestionJob:
        values = dict(row)  # SQLAlchemy RowMapping and test doubles both support mapping conversion.
        return IngestionJob(
            job_id=values["job_id"],
            idempotency_key=values["idempotency_key"],
            provider_id=values["provider_id"],
            operation=values["operation"],
            code=values["code"],
            cursor=values["cursor"],
            replay_id=values["replay_id"],
            page_size=values["page_size"],
            attempt=values["attempt"],
            max_attempts=values["max_attempts"],
            status=values["status"],
            available_at=values["available_at"],
            lease_owner=values["lease_owner"],
            lease_until=values["lease_until"],
            records_persisted=values["records_persisted"],
            records_skipped=values["records_skipped"],
            records_quarantined=values["records_quarantined"],
            error=values["error"],
            created_at=values["created_at"],
            started_at=values["started_at"],
            finished_at=values["finished_at"],
            continuation_job_id=values["continuation_job_id"],
        )


class SyntheticIngestionWorker:
    """Run bounded, replayable work against a synthetic adapter only."""

    def __init__(
        self,
        adapter: ContractedProviderAdapter,
        *,
        store: IngestionStore | None = None,
        clock: Callable[[], datetime] = _utc_now,
        default_max_attempts: int = 3,
        worker_id: str = "synthetic-local-worker",
        lease_seconds: int = 60,
    ) -> None:
        if adapter.capabilities.data_mode != "SYNTHETIC_ONLY" or adapter.capabilities.rights_state != "SYNTHETIC":
            raise ValueError("the local worker accepts synthetic-only adapters")
        if default_max_attempts < 1:
            raise ValueError("default_max_attempts must be positive")
        if not worker_id.strip():
            raise ValueError("worker_id is required")
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        self.adapter = adapter
        self.store = store or InMemoryIngestionStore()
        self.clock = clock
        self.default_max_attempts = default_max_attempts
        self.worker_id = worker_id
        self.lease_seconds = lease_seconds

    def enqueue(
        self,
        *,
        code: str,
        operation: ProviderOperation = "GET_MARKETS",
        cursor: str | None = None,
        page_size: int = 100,
        replay_id: str = "default",
        max_attempts: int | None = None,
    ) -> IngestionJob:
        if not replay_id.strip():
            raise ValueError("replay_id is required")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100")
        idempotency_key = self._idempotency_key(code, operation, cursor, replay_id)
        job = IngestionJob(
            idempotency_key=idempotency_key,
            provider_id=self.adapter.capabilities.provider_id,
            operation=operation,
            code=code,
            cursor=cursor,
            replay_id=replay_id,
            page_size=page_size,
            max_attempts=max_attempts or self.default_max_attempts,
        )
        return self.store.enqueue_job(job)

    def run_next(self) -> IngestionJob | None:
        job = self.store.claim_next(self.worker_id, lease_seconds=self.lease_seconds, now=self.clock())
        if job is None:
            return None
        try:
            page = self.adapter.fetch(
                job.operation,
                code=job.code,
                cursor=job.cursor,
                page_size=job.page_size,
            )
        except Exception as exc:  # provider transport and contract failures are job outcomes
            return self._handle_failure(job, exc)

        persisted = skipped = quarantined = 0
        for record in page.records:
            result = ingest_raw_envelope(record.model_dump(mode="json"))
            if result.quarantine is not None:
                self.store.append_quarantine(result.quarantine)
                quarantined += 1
                continue
            assert result.envelope is not None
            disposition = self.store.append_envelope(result.envelope)
            if disposition == "PERSISTED":
                persisted += 1
            elif disposition == "DUPLICATE":
                skipped += 1
            else:
                quarantined += 1

        continuation_job_id = None
        if page.next_cursor is not None:
            continuation = self.enqueue(
                code=job.code,
                operation=job.operation,
                cursor=page.next_cursor,
                page_size=job.page_size,
                replay_id=job.replay_id,
                max_attempts=job.max_attempts,
            )
            continuation_job_id = continuation.job_id

        finished_at = self.clock()
        return self.store.mark_succeeded(
            job.job_id,
            records_persisted=persisted,
            records_skipped=skipped,
            records_quarantined=quarantined,
            continuation_job_id=continuation_job_id,
            finished_at=finished_at,
        )

    def run_until_idle(self, *, max_jobs: int = 1000) -> IngestionRunSummary:
        if max_jobs < 1:
            raise ValueError("max_jobs must be positive")
        processed = succeeded = failed = quarantined_jobs = persisted = skipped = quarantined = 0
        while processed < max_jobs:
            job = self.run_next()
            if job is None:
                break
            processed += 1
            succeeded += job.status == "SUCCEEDED"
            failed += job.status == "FAILED"
            quarantined_jobs += job.status == "QUARANTINED"
            persisted += job.records_persisted
            skipped += job.records_skipped
            quarantined += job.records_quarantined
        else:
            if self.store.has_pending():
                raise RuntimeError("ingestion run exceeded max_jobs")
        return IngestionRunSummary(
            jobs_processed=processed,
            jobs_succeeded=succeeded,
            jobs_failed=failed,
            jobs_quarantined=quarantined_jobs,
            envelopes_persisted=persisted,
            envelopes_skipped=skipped,
            records_quarantined=quarantined,
        )

    def _handle_failure(self, job: IngestionJob, error: Exception) -> IngestionJob:
        next_attempt = job.attempt
        detail = f"{type(error).__name__}: {error}"
        if next_attempt < job.max_attempts:
            return self.store.mark_retryable(
                job.job_id,
                error=detail,
                available_at=self.clock() + timedelta(seconds=min(60, 2**next_attempt)),
            )
        return self.store.mark_failed(
            job.job_id,
            error=detail,
            finished_at=self.clock(),
        )

    def _idempotency_key(
        self,
        code: str,
        operation: ProviderOperation,
        cursor: str | None,
        replay_id: str,
    ) -> str:
        return "|".join(
            (
                self.adapter.capabilities.provider_id,
                operation,
                code,
                replay_id,
                cursor or "ROOT",
            )
        )
