from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.forecast_archive import ForecastArchive, ImmutableArchiveError, create_forecast_manifest, verify_manifest


ROOT = Path(__file__).resolve().parents[3]


def manifest(output: object = {"probabilities": {"entry-1": 1.0}}):
    return create_forecast_manifest(
        forecast_id="forecast-1",
        race_id="race-1",
        field_revision="field-r1",
        cutoff="2026-01-15T03:30:00Z",
        feature_snapshot={"target_distance": 1200, "entry-1": {"support": 3}},
        model_descriptor={"model_id": "B1_FORM_HEURISTIC", "model_version": "b1-form-v1", "smoothing": 0.1},
        active_runner_ids=["entry-1"],
        data_mode="SYNTHETIC_ONLY",
        diagnostic_flags=["PRE_CUTOFF_RUNS_ONLY"],
        output=output,
    )


def test_manifest_stores_required_hashes_and_is_reproducible() -> None:
    first = manifest()
    second = manifest()

    assert first.to_dict() == second.to_dict()
    assert len(first.feature_snapshot_hash) == 64
    assert len(first.model_hash) == 64
    assert len(first.active_runner_hash) == 64
    assert len(first.manifest_hash) == 64
    verify_manifest(first.to_dict())


def test_archive_is_append_only_and_replayable() -> None:
    archive = ForecastArchive()
    original = manifest()
    archive.append(original)
    archive.append(original)

    assert len(archive) == 1
    assert archive.replay_matches("forecast-1", {"probabilities": {"entry-1": 1.0}})
    assert not archive.replay_matches("forecast-1", {"probabilities": {"entry-1": 0.5}})
    with pytest.raises(ImmutableArchiveError, match="immutable"):
        archive.append(manifest({"probabilities": {"entry-1": 0.5}}))


def test_manifest_verification_detects_tampering() -> None:
    record = manifest().to_dict()
    record["output"] = {"probabilities": {"entry-1": 0.0}}

    with pytest.raises(ImmutableArchiveError, match="manifest hash mismatch"):
        verify_manifest(record)


def test_committed_archive_contains_all_forecast_metadata() -> None:
    archive = json.loads((ROOT / "fixtures" / "synthetic" / "forecast_archive.json").read_text(encoding="utf-8"))

    assert archive["schema_version"] == "ril-024-forecast-archive-v1"
    assert archive["invalidation_policy"]["SCRATCHING"] == "INVALIDATE_PRIOR_CREATE_NEW_REVISION"
    assert archive["invalidation_policy"]["COUPLED_ENTRY"] == "ABSTAIN"
    assert len(archive["records"]) == 6
    for record in archive["records"]:
        assert record["field_revision"]
        assert record["cutoff"]
        assert record["feature_snapshot_hash"]
        assert record["model_hash"]
        assert record["active_runner_hash"]
        assert record["data_mode"] == "SYNTHETIC_ONLY"
        assert record["diagnostic_flags"]
        verify_manifest(record)
