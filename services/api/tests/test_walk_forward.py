from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from app.walk_forward import RaceObservation, build_walk_forward_splits, split_manifest


ROOT = Path(__file__).resolve().parents[3]


def observations(count: int = 6) -> list[RaceObservation]:
    return [RaceObservation(f"race-{index}", datetime(2026, 1, index, tzinfo=timezone.utc), "THOROUGHBRED") for index in range(1, count + 1)]


def test_expanding_windows_are_chronological_disjoint_and_grow() -> None:
    folds = build_walk_forward_splits(
        observations(), initial_train_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        initial_train_end=datetime(2026, 1, 3, tzinfo=timezone.utc),
        calibration_duration=timedelta(days=1), test_duration=timedelta(days=1), step=timedelta(days=1),
    )

    assert len(folds) == 3
    assert folds[0].training_race_ids == ("race-1", "race-2")
    assert folds[0].calibration_race_ids == ("race-3",)
    assert folds[0].test_race_ids == ("race-4",)
    assert len(folds[1].training_race_ids) > len(folds[0].training_race_ids)
    for fold in folds:
        groups = [set(fold.training_race_ids), set(fold.calibration_race_ids), set(fold.test_race_ids)]
        assert not groups[0] & groups[1]
        assert not groups[0] & groups[2]
        assert not groups[1] & groups[2]


def test_rolling_windows_bound_training_history() -> None:
    folds = build_walk_forward_splits(
        observations(), initial_train_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        initial_train_end=datetime(2026, 1, 3, tzinfo=timezone.utc),
        calibration_duration=timedelta(days=1), test_duration=timedelta(days=1), step=timedelta(days=1),
        mode="ROLLING", rolling_train_duration=timedelta(days=2),
    )

    assert folds[0].training_race_ids == ("race-1", "race-2")
    assert folds[1].training_race_ids == ("race-2", "race-3")


def test_split_rejects_duplicate_ids_and_naive_timestamps() -> None:
    with pytest.raises(ValueError, match="race IDs must be unique"):
        build_walk_forward_splits(observations() + [observations()[0]], initial_train_end=datetime(2026, 1, 3, tzinfo=timezone.utc), calibration_duration=timedelta(days=1), test_duration=timedelta(days=1), step=timedelta(days=1))
    with pytest.raises(ValueError, match="timezone-aware"):
        build_walk_forward_splits([RaceObservation("race-1", datetime(2026, 1, 1), "THOROUGHBRED")], initial_train_end=datetime(2026, 1, 1, tzinfo=timezone.utc), calibration_duration=timedelta(days=1), test_duration=timedelta(days=1), step=timedelta(days=1))


def test_split_manifest_is_deterministic_and_records_fixture_limitation() -> None:
    folds = build_walk_forward_splits(observations(), initial_train_end=datetime(2026, 1, 3, tzinfo=timezone.utc), calibration_duration=timedelta(days=1), test_duration=timedelta(days=1), step=timedelta(days=1))
    first = split_manifest(folds)
    second = split_manifest(folds)

    assert first == second
    assert len(first["manifest_hash"]) == 64

    fixture_manifest = json.loads((ROOT / "fixtures" / "synthetic" / "walk_forward_v1.json").read_text(encoding="utf-8"))
    assert fixture_manifest["fixture_race_count"] == 6
    assert "no pre-demo training races" in fixture_manifest["coverage_note"]

