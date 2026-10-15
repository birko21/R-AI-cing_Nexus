"""End-to-end proof for the local synthetic data and forecast path.

This module intentionally stops before any UI, live provider, wagering, or
promotion boundary.  It proves that the provider-shaped fixture can be
ingested, replayed idempotently, transformed into a pre-race baseline forecast,
archived immutably, and held by the release gate.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from app.baseline import BaselineRace, BaselineRunner, build_b0_forecast
from app.betfair_mock import SyntheticBetfairExchangeAdapter, synthetic_betfair_markets
from app.forecast_archive import ForecastArchive, create_forecast_manifest, verify_manifest
from app.ingestion import InMemoryIngestionStore, SyntheticIngestionWorker
from app.providers import ContractedProviderAdapter
from app.release_gate import ReleaseGateInputs, build_release_gate_report, verify_release_gate_report


def run_synthetic_vertical_proof() -> dict[str, Any]:
    """Run the executable local proof and return machine-readable evidence."""

    adapter = ContractedProviderAdapter(SyntheticBetfairExchangeAdapter())
    store = InMemoryIngestionStore()
    worker = SyntheticIngestionWorker(adapter, store=store, worker_id="synthetic-acceptance-proof")

    for code in ("THOROUGHBRED", "HARNESS", "GREYHOUND"):
        worker.enqueue(code=code, page_size=1, replay_id="vertical-proof-primary")
    first = worker.run_until_idle()

    for code in ("THOROUGHBRED", "HARNESS", "GREYHOUND"):
        worker.enqueue(code=code, page_size=1, replay_id="vertical-proof-replay")
    replay = worker.run_until_idle()

    market = synthetic_betfair_markets()[0]
    envelope = next(
        item for item in store.raw_envelopes.values()
        if item.payload["market_catalogue"]["market_id"] == market.market_id
    )
    cutoff = market.market_start_time - timedelta(minutes=5)
    race = BaselineRace(
        race_id=market.race_id,
        code=market.code,
        field_revision=market.field_revision,
        field_status="FINAL_FIELDS",
        runners=tuple(
            BaselineRunner(entry_id=runner.entry_id, number=index)
            for index, runner in enumerate(market.runners, start=1)
        ),
    )
    forecast = build_b0_forecast(
        race,
        cutoff=cutoff,
        manifest_checksum=envelope.payload_sha256,
    )
    assert forecast.status == "READY"

    archive = ForecastArchive()
    manifest = create_forecast_manifest(
        forecast_id=forecast.forecast_id,
        race_id=forecast.race_id,
        field_revision=forecast.field_revision,
        cutoff=forecast.cutoff,
        feature_snapshot={
            "source_envelope_id": envelope.envelope_id,
            "source_payload_sha256": envelope.payload_sha256,
            "market_id": market.market_id,
            "code": market.code,
            "data_mode": envelope.data_mode,
            "pre_race_cutoff": forecast.cutoff,
        },
        model_descriptor={
            "model_id": forecast.model_id,
            "model_version": forecast.model_version,
            "model_status": forecast.model_status,
        },
        active_runner_ids=[runner.entry_id for runner in market.runners],
        data_mode=forecast.data_mode,
        diagnostic_flags=forecast.diagnostics,
        output=forecast.to_dict(),
    )
    archive.append_ready(manifest, forecast_status=forecast.status)
    verify_manifest(archive.get(forecast.forecast_id))
    archive_replay_matches = archive.replay_matches(forecast.forecast_id, forecast.to_dict())

    release_gate = build_release_gate_report(
        ReleaseGateInputs(local_evidence_complete=True, automated_checks_passed=True)
    )
    verify_release_gate_report(release_gate)

    result = {
        "proof_version": "synthetic-vertical-v1",
        "status": "PASS",
        "ingestion": {
            "first_run": first.model_dump(mode="json"),
            "replay_run": replay.model_dump(mode="json"),
            "stored_envelopes": len(store.raw_envelopes),
            "stored_quarantines": len(store.quarantine_records),
        },
        "forecast": {
            "status": forecast.status,
            "model_id": forecast.model_id,
            "runner_count": len(forecast.runners),
            "manifest_hash": manifest.manifest_hash,
            "archive_replay_matches": archive_replay_matches,
        },
        "release_gate": {
            "status": release_gate["status"],
            "activation_authority": release_gate["activation_authority"],
            "promotion_authority": release_gate["promotion_authority"],
            "external_connectivity_enabled": release_gate["external_connectivity_enabled"],
            "wagering_enabled": release_gate["wagering_enabled"],
        },
    }
    assert first.jobs_succeeded == 3
    assert first.envelopes_persisted == 3
    assert replay.jobs_succeeded == 3
    assert replay.envelopes_skipped == 3
    assert len(store.raw_envelopes) == 3
    assert len(store.quarantine_records) == 0
    assert archive_replay_matches is True
    assert release_gate["status"] == "LOCAL_SYNTHETIC_ONLY_HOLD"
    assert release_gate["activation_authority"] == "NONE"
    assert release_gate["promotion_authority"] == "NONE"
    return result
