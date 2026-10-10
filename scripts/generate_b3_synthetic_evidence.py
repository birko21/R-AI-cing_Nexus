"""Train the pinned B3 backends on synthetic rows and write non-predictive evidence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.historical_evaluation import ForecastCase, evaluate_forecasts  # noqa: E402
from app.ml_models import FeatureSchema, TrainingRow, load_b3_artifact, train_b3_model  # noqa: E402


OUT = ROOT / "docs" / "evidence" / "ril-061" / "b3-synthetic-evaluation.json"
UTC = timezone.utc
FEATURES = ("recent_form", "adjusted_speed", "distance_suitability", "fitness")
CODES = ("THOROUGHBRED", "HARNESS", "GREYHOUND")


def training_rows(code: str, schema: FeatureSchema) -> tuple[TrainingRow, ...]:
    rows: list[TrainingRow] = []
    for day in range(1, 9):
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


def main() -> None:
    evidence: list[dict[str, object]] = []
    cases: list[ForecastCase] = []
    with tempfile.TemporaryDirectory(prefix="ril061-b3-") as temp_dir:
        for code in CODES:
            schema = FeatureSchema(code, "FORM_ONLY", FEATURES)
            for backend in ("lightgbm", "catboost"):
                model = train_b3_model(rows=training_rows(code, schema), schema=schema, backend=backend, seed=1729, created_at=datetime(2026, 1, 20, tzinfo=UTC))
                artifact_path = Path(temp_dir) / f"{code.lower()}-{backend}.json"
                envelope = model.save_artifact(artifact_path)
                restored = load_b3_artifact(artifact_path)
                race_id = f"{code.lower()}-test-09-{backend}"
                cutoff = datetime(2026, 1, 9, 1, tzinfo=UTC)
                eligible = {f"runner-{runner}": cutoff - timedelta(hours=1) for runner in range(4)}
                features = {
                    f"runner-{runner}": {name: (4.0 if runner == 0 else 0.5 + runner / 10) - (index / 10) for index, name in enumerate(FEATURES)}
                    for runner in range(4)
                }
                prediction = restored.predict(race_id=race_id, entry_features=features, cutoff=cutoff, eligible_at=eligible)
                evidence.append({
                    "code": code, "backend": backend, "state": prediction.state,
                    "model_status": prediction.model_status, "artifact_id": envelope["artifact_id"],
                    "artifact_sha256": envelope["artifact_sha256"], "model_version": prediction.model_version,
                    "feature_schema_hash": prediction.feature_schema_hash,
                    "training_manifest_hash": prediction.training_manifest_hash,
                    "probabilities": prediction.probabilities,
                    "race_probability_sum": sum(prediction.probabilities.values()),
                    "data_mode": "SYNTHETIC_ONLY",
                })
                if prediction.state == "READY":
                    cases.append(ForecastCase(
                        race_id=race_id, code=code, observed_at=cutoff, model_id=prediction.model_id,
                        model_version=prediction.model_version, probabilities=prediction.probabilities,
                        winner_entry_id="runner-0", outcome_status="SINGLE_WINNER", feature_family="FORM_ONLY",
                        fold_id=f"fold-{code.lower()}-{backend}", fold_role="TEST", data_mode="SYNTHETIC_ONLY",
                    ))
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
