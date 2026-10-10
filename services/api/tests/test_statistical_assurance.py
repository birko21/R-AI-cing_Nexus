from datetime import datetime, timedelta, timezone

import pytest

from app.ml_models import FeatureSchema, TrainingRow
from app.statistical_assurance import (
    ChoiceModel,
    RaceTemperatureCalibrator,
    ablate_and_retrain,
    make_fold_assurance_record,
)
from app.walk_forward import RaceObservation, build_walk_forward_splits


UTC = timezone.utc
SCHEMA = FeatureSchema("THOROUGHBRED", "FORM_ONLY", ("recent_form", "speed"))


def rows() -> tuple[TrainingRow, ...]:
    rows = []
    for race_number, day in enumerate((1, 2), 1):
        cutoff = datetime(2026, 1, day, 12, tzinfo=UTC)
        for entry, form, winner in (("a", 2.0, True), ("b", 0.0, False)):
            rows.append(TrainingRow(f"race-{race_number}", entry, "THOROUGHBRED", "FORM_ONLY", cutoff, cutoff - timedelta(hours=1), {"recent_form": form, "speed": form}, winner, "SYNTHETIC_ONLY", (f"receipt-{race_number}-{entry}",), SCHEMA.schema_hash))
    return tuple(rows)


def test_fold_record_contains_exact_membership_and_hashes() -> None:
    folds = build_walk_forward_splits(
        [RaceObservation(f"race-{i}", datetime(2026, 1, i, tzinfo=UTC), "THOROUGHBRED") for i in range(1, 7)],
        initial_train_end=datetime(2026, 1, 3, tzinfo=UTC), calibration_duration=timedelta(days=1), test_duration=timedelta(days=1), step=timedelta(days=1),
    )
    record = make_fold_assurance_record(folds[0], dataset_hash="d" * 64, training_feature_snapshot_hashes=("a" * 64,), model_artifact_id="model", calibration_artifact_id="cal", test_artifact_id="test")
    assert record.training_race_ids == ("race-1", "race-2")
    assert record.training_cutoff.endswith("Z")
    assert len(record.record_hash) == 64


def test_temperature_calibration_is_race_level_and_held_out() -> None:
    calibrator = RaceTemperatureCalibrator.fit((("cal-1", {"a": 0.8, "b": 0.2}, "a"), ("cal-2", {"a": 0.6, "b": 0.4}, "b")))
    result = calibrator.apply({"a": 0.7, "b": 0.3})
    assert calibrator.calibration_race_ids == ("cal-1", "cal-2")
    assert sum(result.values()) == pytest.approx(1.0)
    assert calibrator.to_dict()["status"] == "HELD_OUT_RACE_LEVEL_CALIBRATION"


def test_ablation_retrains_with_a_new_schema_and_artifact() -> None:
    called = {}

    def trainer(ablated_rows, schema):
        called["rows"] = ablated_rows
        called["schema"] = schema
        return "artifact-without-speed"

    result = ablate_and_retrain(rows(), SCHEMA, feature_family_by_name={"recent_form": "FORM", "speed": "SPEED"}, removed_feature_family="SPEED", trainer=trainer)
    assert result.retained_feature_names == ("recent_form",)
    assert called["schema"].feature_names == ("recent_form",)
    assert all(set(row.feature_values) == {"recent_form"} for row in called["rows"])
    assert result.retrained_model_artifact_id == "artifact-without-speed"


def test_choice_model_is_an_independent_race_level_challenger() -> None:
    model = ChoiceModel.fit(rows(), SCHEMA)
    probabilities = model.predict({"a": {"recent_form": 2.0, "speed": 2.0}, "b": {"recent_form": 0.0, "speed": 0.0}})
    assert sum(probabilities.values()) == pytest.approx(1.0)
    assert probabilities["a"] > probabilities["b"]
