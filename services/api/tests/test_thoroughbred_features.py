from datetime import datetime, timezone

import pytest

from app.thoroughbred_features import SPECIALIST_FEATURES, ThoroughbredFact, materialize_thoroughbred_features


CUTOFF = datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc)


def fact(receipt: str, observed_at: datetime, **overrides: object) -> ThoroughbredFact:
    values: dict[str, object] = {
        "participant_id": "p1", "observed_at": observed_at, "source_receipt_id": receipt,
        "class_band": "BM", "distance": 1200, "track_going": "GOOD4", "barrier": 3,
        "weight_kg": 57.0, "pace_rating": 81.0, "sectional_time": 34.2,
    }
    values.update(overrides)
    return ThoroughbredFact(**values)


def test_specialist_features_are_descriptive_and_provenance_preserving() -> None:
    snapshot = materialize_thoroughbred_features(
        race_id="race-1", participant_id="p1", cutoff=CUTOFF, target_class="BM", target_distance=1200,
        target_track_going="GOOD4", facts=[fact("receipt-1", datetime(2025, 12, 1, tzinfo=timezone.utc)), fact("receipt-future", datetime(2026, 1, 15, 12, tzinfo=timezone.utc), pace_rating=99.0)],
    )
    assert set(snapshot.features) == set(SPECIALIST_FEATURES)
    assert snapshot.features["class_match_rate"].value == 1.0
    assert snapshot.features["sectional_time"].value == 34.2
    assert snapshot.included_receipt_ids == ("receipt-1",)
    assert snapshot.excluded_future_receipt_ids == ("receipt-future",)
    assert snapshot.attribution_status == "DESCRIPTIVE_ASSOCIATION_ONLY"


def test_missing_specialist_inputs_are_null_with_reasons_and_receipts() -> None:
    snapshot = materialize_thoroughbred_features(
        race_id="race-1", participant_id="p1", cutoff=CUTOFF, target_class=None, target_distance=None,
        target_track_going=None, facts=[fact("receipt-1", datetime(2025, 12, 1, tzinfo=timezone.utc), class_band=None, distance=None, track_going=None, barrier=None, weight_kg=None, pace_rating=None, sectional_time=None)],
    )
    assert snapshot.features["class_match_rate"].missing_reason == "MISSING_TARGET_CLASS"
    assert snapshot.features["distance_match_rate"].missing_reason == "MISSING_TARGET_DISTANCE"
    assert snapshot.features["barrier_position"].source_receipt_ids == ("receipt-1",)


def test_empty_history_and_invalid_modes_fail_closed() -> None:
    snapshot = materialize_thoroughbred_features(
        race_id="race-1", participant_id="p1", cutoff=CUTOFF, target_class="BM", target_distance=1200,
        target_track_going="GOOD4", facts=[],
    )
    assert all(feature.missing_reason == "NO_PRE_CUTOFF_SUPPORT" for feature in snapshot.features.values())
    with pytest.raises(ValueError, match="timezone-aware"):
        materialize_thoroughbred_features(race_id="race-1", participant_id="p1", cutoff=datetime(2026, 1, 15), target_class=None, target_distance=None, target_track_going=None, facts=[])
    with pytest.raises(ValueError, match="data_mode"):
        materialize_thoroughbred_features(race_id="race-1", participant_id="p1", cutoff=CUTOFF, target_class=None, target_distance=None, target_track_going=None, facts=[], data_mode="LICENSED")
