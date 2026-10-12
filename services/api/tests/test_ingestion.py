from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.betfair_mock import SyntheticBetfairExchangeAdapter, synthetic_betfair_markets
from app.ingestion import InMemoryIngestionStore, IngestionJob, PostgresIngestionStore, SyntheticIngestionWorker
from app.providers import ContractedProviderAdapter


def worker(adapter=None, *, store=None):
    return SyntheticIngestionWorker(
        ContractedProviderAdapter(adapter or SyntheticBetfairExchangeAdapter()),
        store=store,
        clock=lambda: datetime(2026, 1, 15, 2, 0, tzinfo=timezone.utc),
    )


def test_worker_ingests_all_three_codes_and_is_idempotent() -> None:
    ingestion = worker()

    initial_jobs = [ingestion.enqueue(code=code) for code in ("THOROUGHBRED", "HARNESS", "GREYHOUND")]
    first = ingestion.run_until_idle()

    assert first.jobs_processed == 3
    assert first.jobs_succeeded == 3
    assert first.envelopes_persisted == 3
    assert len(ingestion.store.raw_envelopes) == 3
    assert all(envelope.data_mode == "SYNTHETIC_ONLY" for envelope in ingestion.store.raw_envelopes.values())
    assert all(envelope.retrieval_metadata["credentials_used"] is False for envelope in ingestion.store.raw_envelopes.values())

    replay_job = ingestion.enqueue(code="THOROUGHBRED")
    assert replay_job.job_id == initial_jobs[0].job_id
    replay = ingestion.run_until_idle()
    assert replay.jobs_processed == 0
    assert len(ingestion.store.raw_envelopes) == 3


def test_worker_processes_pagination_and_skips_same_checksum_replay() -> None:
    markets = synthetic_betfair_markets()
    adapter = SyntheticBetfairExchangeAdapter((markets[0], replace(markets[0], market_id="bf.au.tb.1004")))
    ingestion = worker(adapter)

    ingestion.enqueue(code="THOROUGHBRED", page_size=1, replay_id="first-run")
    summary = ingestion.run_until_idle()
    assert summary.jobs_processed == 2
    assert summary.envelopes_persisted == 2
    assert len(ingestion.store.raw_envelopes) == 2

    ingestion.enqueue(code="THOROUGHBRED", page_size=1, replay_id="second-run")
    replay = ingestion.run_until_idle()
    assert replay.jobs_processed == 2
    assert replay.envelopes_persisted == 0
    assert replay.envelopes_skipped == 2
    assert len(ingestion.store.raw_envelopes) == 2


def test_worker_retries_then_records_terminal_failure() -> None:
    class FailingAdapter(SyntheticBetfairExchangeAdapter):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def fetch(self, *args, **kwargs):
            self.calls += 1
            raise RuntimeError("synthetic transport unavailable")

    ingestion = worker(FailingAdapter())
    ingestion.enqueue(code="THOROUGHBRED", max_attempts=2)
    summary = ingestion.run_until_idle()

    assert summary.jobs_processed == 2
    assert summary.jobs_failed == 1
    job = next(iter(ingestion.store.jobs.values()))
    assert job.status == "FAILED"
    assert job.attempt == 2
    assert "synthetic transport unavailable" in (job.error or "")


def test_worker_rejects_non_synthetic_adapter() -> None:
    adapter = ContractedProviderAdapter(SyntheticBetfairExchangeAdapter())
    adapter.capabilities = replace(adapter.capabilities, data_mode="LICENSED")
    with pytest.raises(ValueError, match="synthetic-only"):
        SyntheticIngestionWorker(adapter)


def test_store_quarantines_same_id_with_changed_payload() -> None:
    store = InMemoryIngestionStore()
    ingestion = worker(store=store)
    ingestion.enqueue(code="THOROUGHBRED")
    ingestion.run_until_idle()
    original = next(iter(store.raw_envelopes.values()))
    changed = original.model_copy(update={"payload": {"changed": True}, "payload_sha256": "0" * 64})

    disposition = store.append_envelope(changed)
    assert disposition == "QUARANTINED"
    assert len(store.quarantine_records) == 1
    assert next(iter(store.quarantine_records.values())).reason_code == "UNRESOLVED_IDENTITY"


def test_worker_projects_persisted_and_replayed_envelopes() -> None:
    projected: list[str] = []
    ingestion = SyntheticIngestionWorker(
        ContractedProviderAdapter(SyntheticBetfairExchangeAdapter()),
        projector=lambda envelope: projected.append(envelope.envelope_id),
    )

    ingestion.enqueue(code="THOROUGHBRED", replay_id="projection-first")
    first = ingestion.run_until_idle()
    ingestion.enqueue(code="THOROUGHBRED", replay_id="projection-replay")
    second = ingestion.run_until_idle()

    assert first.envelopes_persisted == 1
    assert second.envelopes_skipped == 1
    assert projected == ["synthetic-betfair:bf.au.tb.1001", "synthetic-betfair:bf.au.tb.1001"]


def test_worker_retries_projection_failures_and_does_not_claim_success() -> None:
    def failing_projector(_envelope) -> None:
        raise RuntimeError("canonical projection unavailable")

    ingestion = SyntheticIngestionWorker(
        ContractedProviderAdapter(SyntheticBetfairExchangeAdapter()),
        projector=failing_projector,
    )
    ingestion.enqueue(code="THOROUGHBRED", max_attempts=2)

    summary = ingestion.run_until_idle()

    assert summary.jobs_failed == 1
    assert summary.envelopes_persisted == 0
    job = next(iter(ingestion.store.jobs.values()))
    assert job.status == "FAILED"
    assert job.attempt == 2
    assert "canonical projection unavailable" in (job.error or "")


def test_postgres_store_job_mapping_is_round_trip_safe() -> None:
    now = datetime(2026, 1, 15, 2, 0, tzinfo=timezone.utc)
    job = IngestionJob(
        idempotency_key="synthetic|GET_MARKETS|THOROUGHBRED|run|ROOT",
        provider_id="betfair-exchange-synthetic",
        operation="GET_MARKETS",
        code="THOROUGHBRED",
        replay_id="run",
        available_at=now,
        created_at=now,
        lease_owner="worker-a",
        lease_until=now,
        status="RUNNING",
        attempt=1,
    )

    mapped = PostgresIngestionStore._job_from_row(job.model_dump())
    assert mapped == job
