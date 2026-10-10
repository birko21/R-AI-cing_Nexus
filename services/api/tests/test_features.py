from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from app.features import HistoricalRunFact, materialize_feature_snapshot


ROOT = Path(__file__).resolve().parents[3]
CUTOFF = datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc)


def fact(receipt: str, observed_at: datetime, *, code: str = "THOROUGHBRED", participant: str = "p1", distance: int | None = 1200, finish: int | None = 2) -> HistoricalRunFact:
    return HistoricalRunFact(participant, code, observed_at, distance, finish, receipt)


def test_features_use_only_pre_cutoff_facts_and_preserve_provenance() -> None:
    before = [fact("receipt-1", datetime(2025, 12, 1, tzinfo=timezone.utc)), fact("receipt-2", datetime(2025, 12, 2, tzinfo=timezone.utc))]
    future = fact("receipt-future", datetime(2026, 1, 15, 12, tzinfo=timezone.utc), finish=1)
    snapshot = materialize_feature_snapshot(race_id="race-1", participant_id="p1", code="THOROUGHBRED", cutoff=CUTOFF, target_distance=1200, facts=[*before, future])
    without_future = materialize_feature_snapshot(race_id="race-1", participant_id="p1", code="THOROUGHBRED", cutoff=CUTOFF, target_distance=1200, facts=before)

    assert snapshot.features["runs_count"].value == 2
    assert snapshot.included_receipt_ids == ("receipt-1", "receipt-2")
    assert snapshot.excluded_future_receipt_ids == ("receipt-future",)
    assert snapshot.features["best_finish_position"].source_receipt_ids == ("receipt-1", "receipt-2")
    assert snapshot.features == without_future.features
    assert snapshot.snapshot_hash != without_future.snapshot_hash


@pytest.mark.parametrize("code,expected", [
    ("THOROUGHBRED", {"distance_match_rate", "finish_consistency"}),
    ("HARNESS", {"distance_match_rate", "recent_finish_rate"}),
    ("GREYHOUND", {"distance_match_rate", "recent_finish_rate"}),
])
def test_common_and_code_specific_feature_schema_is_versioned(code: str, expected: set[str]) -> None:
    snapshot = materialize_feature_snapshot(
        race_id="race-1", participant_id="p1", code=code, cutoff=CUTOFF, target_distance=1200,
        facts=[fact("receipt-1", datetime(2025, 12, 1, tzinfo=timezone.utc), code=code), fact("receipt-2", datetime(2025, 12, 2, tzinfo=timezone.utc), code=code)],
    )

    assert snapshot.schema_version == "features-v1"
    assert {"runs_count", "mean_finish_position", "best_finish_position"}.issubset(snapshot.features)
    assert expected.issubset(snapshot.features)


def test_missing_support_is_explicit_and_not_filled() -> None:
    snapshot = materialize_feature_snapshot(race_id="race-1", participant_id="p1", code="GREYHOUND", cutoff=CUTOFF, target_distance=1200, facts=[])

    assert snapshot.features["runs_count"].missing is True
    assert snapshot.features["runs_count"].value is None
    assert snapshot.features["runs_count"].missing_reason == "NO_PRE_CUTOFF_SUPPORT"
    assert snapshot.included_receipt_ids == tuple()


def test_missing_fields_retain_missingness_reason() -> None:
    snapshot = materialize_feature_snapshot(
        race_id="race-1", participant_id="p1", code="HARNESS", cutoff=CUTOFF, target_distance=None,
        facts=[fact("receipt-1", datetime(2025, 12, 1, tzinfo=timezone.utc), code="HARNESS", distance=None, finish=None), fact("receipt-2", datetime(2025, 12, 2, tzinfo=timezone.utc), code="HARNESS", distance=None, finish=None)],
    )

    assert snapshot.features["mean_finish_position"].missing_reason == "MISSING_FINISH_POSITION"
    assert snapshot.features["distance_match_rate"].missing_reason == "MISSING_TARGET_DISTANCE"


def test_cutoff_must_be_timezone_aware_and_code_supported() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        materialize_feature_snapshot(race_id="race-1", participant_id="p1", code="THOROUGHBRED", cutoff=datetime(2026, 1, 15), target_distance=1200, facts=[])
    with pytest.raises(ValueError, match="unsupported feature code"):
        materialize_feature_snapshot(race_id="race-1", participant_id="p1", code="UNKNOWN", cutoff=CUTOFF, target_distance=1200, facts=[])


def test_feature_manifest_fixture_is_deterministic_and_complete() -> None:
    manifest = json.loads((ROOT / "fixtures" / "synthetic" / "features_v1.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "features-v1"
    assert manifest["record_count"] == 24
    assert manifest["cutoff"] == "2026-01-15T03:30:00Z"
    assert all(record["snapshot_hash"] for record in manifest["records"])
    assert all(record["included_receipt_ids"] for record in manifest["records"])
