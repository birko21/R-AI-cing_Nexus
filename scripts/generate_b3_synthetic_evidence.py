"""Train the pinned B3 backends on synthetic rows and write non-predictive evidence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import hashlib
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.historical_evaluation import ForecastCase, evaluate_forecasts  # noqa: E402
from app.ml_models import FeatureSchema, TrainingRow, load_b3_artifact, train_b3_model  # noqa: E402
from app.statistical_assurance import RaceTemperatureCalibrator, ablate_and_retrain, make_fold_assurance_record  # noqa: E402
from app.walk_forward import RaceObservation, build_walk_forward_splits  # noqa: E402


OUT = ROOT / "docs" / "evidence" / "ril-061" / "b3-synthetic-evaluation.json"
UTC = timezone.utc
FEATURES = ("recent_form", "adjusted_speed", "distance_suitability", "fitness")
CODES = ("THOROUGHBRED", "HARNESS", "GREYHOUND")


def training_rows(code: str, schema: FeatureSchema, first_day: int = 1, last_day: int = 5) -> tuple[TrainingRow, ...]:
    rows: list[TrainingRow] = []
    for day in range(first_day, last_day + 1):
        cutoff = datetime(2026, 1, day, 1, tzinfo=UTC)
        eligible = cutoff - timedelta(hours=2)
        winner = day % 4
        for runner in range(4):
            signal = 4.0 if runner == winner else 0.5 + (runner / 10)
            values = {name: signal - (index / 10) for index, name in enumerate(FEATURES)}
            rows.append(TrainingRow(
                f"{code.lower()}-train-{day}", f"runner-{runner}", code, "FORM_ONLY", cutoff,
                eligible, values, runner == winner, "SYNTHETIC_ONLY", (f"synthetic-{code.lower()}-{day}-{runner}",), schema.schema_hash,
            ))
    return tuple(rows)


def forecast_inputs(code: str, day: int) -> tuple[datetime, dict[str, datetime], dict[str, dict[str, float]], str]:
    cutoff = datetime(2026, 1, day, 1, tzinfo=UTC)
    eligible = {f"runner-{runner}": cutoff - timedelta(hours=1) for runner in range(4)}
    winner = day % 4
    features = {
        f"runner-{runner}": {name: (4.0 if runner == winner else 0.5 + runner / 10) - (index / 10) for index, name in enumerate(FEATURES)}
        for runner in range(4)
    }
    return cutoff, eligible, features, f"{code.lower()}-race-{day}"


def main() -> None:
    evidence: list[dict[str, object]] = []
    cases: list[ForecastCase] = []
    with tempfile.TemporaryDirectory(prefix="ril061-b3-") as temp_dir:
        for code in CODES:
            schema = FeatureSchema(code, "FORM_ONLY", FEATURES)
            observations = [RaceObservation(f"{code.lower()}-race-{day}", datetime(2026, 1, day, 1, tzinfo=UTC), code) for day in range(1, 10)]
            fold = build_walk_forward_splits(
                observations, initial_train_end=datetime(2026, 1, 6, 1, tzinfo=UTC),
                calibration_duration=timedelta(days=1), test_duration=timedelta(days=3), step=timedelta(days=3),
            )[0]
            for backend in ("lightgbm", "catboost"):
                model = train_b3_model(rows=training_rows(code, schema), schema=schema, backend=backend, seed=1729, created_at=datetime(2026, 1, 20, tzinfo=UTC))
                artifact_path = Path(temp_dir) / f"{code.lower()}-{backend}.json"
                envelope = model.save_artifact(artifact_path)
                restored = load_b3_artifact(artifact_path, trusted_manifest=model.training_manifest)
                calibration_cutoff, calibration_eligible, calibration_features, calibration_race_id = forecast_inputs(code, 6)
                calibration_prediction = restored.predict(race_id=calibration_race_id, entry_features=calibration_features, cutoff=calibration_cutoff, eligible_at=calibration_eligible)
                calibrator = RaceTemperatureCalibrator.fit(((calibration_race_id, calibration_prediction.probabilities, "runner-2"),))
                ablation = ablate_and_retrain(
                    training_rows(code, schema), schema,
                    feature_family_by_name={"recent_form": "FORM", "adjusted_speed": "SPEED", "distance_suitability": "DISTANCE", "fitness": "FITNESS"},
                    removed_feature_family="DISTANCE",
                    trainer=lambda ablated_rows, ablated_schema: train_b3_model(rows=ablated_rows, schema=ablated_schema, backend=backend, seed=1729, created_at=datetime(2026, 1, 20, tzinfo=UTC)).artifact_id,
                )
                training_dataset_hash = hashlib.sha256(json.dumps({"rows": [row.feature_snapshot_hash for row in training_rows(code, schema)], "fold": fold.to_dict()}, sort_keys=True).encode("utf-8")).hexdigest()
                fold_record = make_fold_assurance_record(
                    fold, dataset_hash=training_dataset_hash, training_feature_snapshot_hashes=model.training_manifest.feature_snapshot_hashes,
                    model_artifact_id=envelope["artifact_id"], calibration_artifact_id=calibrator.artifact_id, test_artifact_id=envelope["artifact_id"],
                )
                test_predictions = []
                for day in fold.test_race_ids:
                    day_number = int(day.rsplit("-", 1)[1])
                    cutoff, eligible, features, race_id = forecast_inputs(code, day_number)
                    raw_prediction = restored.predict(race_id=race_id, entry_features=features, cutoff=cutoff, eligible_at=eligible)
                    prediction_probabilities = calibrator.apply(raw_prediction.probabilities)
                    prediction = raw_prediction
                    test_predictions.append((race_id, cutoff, prediction_probabilities, day_number % 4))
                    cases.append(ForecastCase(
                        race_id=race_id, code=code, observed_at=cutoff, model_id=prediction.model_id,
                        model_version=prediction.model_version, probabilities=prediction_probabilities,
                        winner_entry_id=f"runner-{day_number % 4}", outcome_status="SINGLE_WINNER", feature_family="FORM_ONLY",
                        fold_id=fold.fold_id, fold_role="TEST", data_mode="SYNTHETIC_ONLY",
                    ))
                evidence.append({
                    "code": code, "backend": backend, "state": prediction.state,
                    "model_status": prediction.model_status, "artifact_id": envelope["artifact_id"],
                    "artifact_sha256": envelope["artifact_sha256"], "model_version": prediction.model_version,
                    "feature_schema_hash": prediction.feature_schema_hash,
                    "training_manifest_hash": prediction.training_manifest_hash,
                    "probabilities": test_predictions[-1][2],
                    "race_probability_sum": sum(test_predictions[-1][2].values()),
                    "data_mode": "SYNTHETIC_ONLY",
                    "calibration": calibrator.to_dict(),
                    "fold_assurance": fold_record.to_dict(),
                    "ablation": {"removed_feature_family": ablation.removed_feature_family, "retrained_model_artifact_id": ablation.retrained_model_artifact_id, "schema_hash": ablation.schema_hash},
                })
    report = evaluate_forecasts(tuple(cases))
    payload = {
        "schema_version": "ril-061-b3-evidence-v1", "status": "ILLUSTRATIVE_SYNTHETIC_ONLY",
        "validated_claim": False, "backends": ["lightgbm", "catboost"],
        "models": evidence, "evaluation": report,
        "limitations": [
            "Synthetic rows are not historical racing data and cannot establish predictive validity.",
            "No provider rights, retention or model-use approval is established.",
            "Artifacts are generated in a temporary directory and are not production model registry entries.",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"B3 SYNTHETIC EVIDENCE VALID: models={len(evidence)} scored_cases={report['scored_case_count']} output={OUT}")


if __name__ == "__main__":
    main()
