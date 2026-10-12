"""Repeat the synthetic data path to expose nondeterminism and replay defects."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.betfair_mock import (  # noqa: E402
    SyntheticBetfairExchangeAdapter,
    build_synthetic_betfair_replay_manifest,
    reconcile_synthetic_betfair_replay_manifest,
)
from app.ingestion import InMemoryIngestionStore, SyntheticIngestionWorker  # noqa: E402
from app.providers import ContractedProviderAdapter  # noqa: E402
from app.synthetic_acceptance import run_synthetic_vertical_proof  # noqa: E402


def main() -> None:
    adapter = ContractedProviderAdapter(SyntheticBetfairExchangeAdapter())
    store = InMemoryIngestionStore()
    worker = SyntheticIngestionWorker(
        adapter,
        store=store,
        worker_id="synthetic-pressure-test",
        clock=lambda: datetime(2026, 1, 15, 2, 0, tzinfo=timezone.utc),
    )
    persisted_by_cycle: list[int] = []
    skipped_by_cycle: list[int] = []
    for cycle in range(25):
        for code in ("THOROUGHBRED", "HARNESS", "GREYHOUND"):
            worker.enqueue(code=code, page_size=1, replay_id=f"pressure-{cycle}")
        summary = worker.run_until_idle()
        persisted_by_cycle.append(summary.envelopes_persisted)
        skipped_by_cycle.append(summary.envelopes_skipped)
        assert summary.jobs_failed == 0
        assert summary.records_quarantined == 0

    assert persisted_by_cycle[0] == 3
    assert all(value == 0 for value in persisted_by_cycle[1:])
    assert all(value == 3 for value in skipped_by_cycle[1:])
    assert len(store.raw_envelopes) == 3

    manifest = build_synthetic_betfair_replay_manifest(page_size=1)
    assert all(build_synthetic_betfair_replay_manifest(page_size=1) == manifest for _ in range(25))

    proof = run_synthetic_vertical_proof()
    archived = proof["forecast"]["manifest_hash"]
    assert isinstance(archived, str) and len(archived) == 64

    tamper_checks = 0
    for _ in range(25):
        mutated = deepcopy(manifest)
        mutated["record_count"] = 999
        report = reconcile_synthetic_betfair_replay_manifest(mutated)
        assert report.status == "MISMATCH"
        assert "record_count differs from deterministic source" in report.mismatches
        tamper_checks += 1

    print(json.dumps({
        "status": "PASS",
        "cycles": 25,
        "stored_envelopes": len(store.raw_envelopes),
        "tamper_cases": tamper_checks,
        "replay_manifest_deterministic": True,
        "vertical_proof_status": proof["status"],
    }, indent=2))


if __name__ == "__main__":
    main()
