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
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
        for field_name in ("created_at", "started_at", "finished_at"):
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

    def next_queued(self) -> IngestionJob | None:
        while self._queued_job_ids:
            job_id = self._queued_job_ids.popleft()
            job = self.jobs[job_id]
            if job.status == "QUEUED":
                return job
        return None

    def has_queued(self) -> bool:
        return any(self.jobs[job_id].status == "QUEUED" for job_id in self._queued_job_ids)

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


class SyntheticIngestionWorker:
    """Run bounded, replayable work against a synthetic adapter only."""

    def __init__(
        self,
        adapter: ContractedProviderAdapter,
        *,
        store: InMemoryIngestionStore | None = None,
        clock: Callable[[], datetime] = _utc_now,
        default_max_attempts: int = 3,
    ) -> None:
        if adapter.capabilities.data_mode != "SYNTHETIC_ONLY" or adapter.capabilities.rights_state != "SYNTHETIC":
            raise ValueError("the local worker accepts synthetic-only adapters")
        if default_max_attempts < 1:
            raise ValueError("default_max_attempts must be positive")
        self.adapter = adapter
        self.store = store or InMemoryIngestionStore()
        self.clock = clock
        self.default_max_attempts = default_max_attempts

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
        return self.store.create_job(job)[0]

    def run_next(self) -> IngestionJob | None:
        job = self.store.next_queued()
        if job is None:
            return None
        started_at = self.clock()
        self.store.update_job(job.job_id, status="RUNNING", started_at=started_at, error=None)
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
        status: JobStatus = "QUARANTINED" if quarantined else "SUCCEEDED"
        return self.store.update_job(
            job.job_id,
            status=status,
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
            if self.store.has_queued():
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
        next_attempt = job.attempt + 1
        detail = f"{type(error).__name__}: {error}"
        if next_attempt < job.max_attempts:
            return self.store.update_job(
                job.job_id,
                status="QUEUED",
                attempt=next_attempt,
                error=detail,
            )
        return self.store.update_job(
            job.job_id,
            status="FAILED",
            attempt=next_attempt,
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
