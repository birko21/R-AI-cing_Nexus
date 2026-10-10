from datetime import datetime, timedelta, timezone
import json

import pytest

from app.ml_models import (
    FeatureSchema,
    ModelArtifactError,
    TrainingRow,
    build_b3_forecast,
    load_b3_artifact,
    train_b3_model,
)
from app.model_benchmarks import BenchmarkRace, BenchmarkRunner


UTC = timezone.utc
SCHEMA = FeatureSchema("THOROUGHBRED", "FORM_ONLY", ("recent_form", "adjusted_speed"))


def rows() -> tuple[TrainingRow, ...]:
    cutoff = datetime(2026, 1, 15, 1, tzinfo=UTC)
    eligible = cutoff - timedelta(hours=1)
    return (
        TrainingRow("race-1", "a", "THOROUGHBRED", "FORM_ONLY", cutoff, eligible, {"recent_form": 2.0, "adjusted_speed": 2.0}, True, "SYNTHETIC_ONLY", ("r1-a",), SCHEMA.schema_hash),
        TrainingRow("race-1", "b", "THOROUGHBRED", "FORM_ONLY", cutoff, eligible, {"recent_form": 0.0, "adjusted_speed": 0.0}, False, "SYNTHETIC_ONLY", ("r1-b",), SCHEMA.schema_hash),
        TrainingRow("race-2", "a", "THOROUGHBRED", "FORM_ONLY", cutoff + timedelta(days=1), eligible + timedelta(days=1), {"recent_form": 1.5, "adjusted_speed": 2.0}, True, "SYNTHETIC_ONLY", ("r2-a",), SCHEMA.schema_hash),
        TrainingRow("race-2", "b", "THOROUGHBRED", "FORM_ONLY", cutoff + timedelta(days=1), eligible + timedelta(days=1), {"recent_form": 0.0, "adjusted_speed": 0.5}, False, "SYNTHETIC_ONLY", ("r2-b",), SCHEMA.schema_hash),
    )


def test_lightgbm_b3_trains_predicts_and_round_trips_an_immutable_artifact(tmp_path) -> None:
    model = train_b3_model(rows=rows(), schema=SCHEMA, backend="lightgbm", seed=7, created_at=datetime(2026, 1, 20, tzinfo=UTC))
    prediction = model.predict(race_id="race-3", entry_features={"a": {"recent_form": 2.0, "adjusted_speed": 1.8}, "b": {"recent_form": 0.1, "adjusted_speed": 0.2}}, cutoff=datetime(2026, 1, 25, tzinfo=UTC), eligible_at={"a": datetime(2026, 1, 25, tzinfo=UTC) - timedelta(minutes=2), "b": datetime(2026, 1, 25, tzinfo=UTC) - timedelta(minutes=2)})
    assert prediction.state == "READY"
    assert sum(prediction.probabilities.values()) == pytest.approx(1.0)
    assert prediction.model_status == "ILLUSTRATIVE_NOT_VALIDATED"
    assert all(0.0 <= probability <= 1.0 for probability in prediction.probabilities.values())

    path = tmp_path / "b3.json"
    envelope = model.save_artifact(path)
    restored = load_b3_artifact(path, trusted_manifest=model.training_manifest)
    restored_prediction = restored.predict(race_id="race-3", entry_features={"a": {"recent_form": 2.0, "adjusted_speed": 1.8}, "b": {"recent_form": 0.1, "adjusted_speed": 0.2}}, cutoff=datetime(2026, 1, 25, tzinfo=UTC), eligible_at={"a": datetime(2026, 1, 25, tzinfo=UTC) - timedelta(minutes=2), "b": datetime(2026, 1, 25, tzinfo=UTC) - timedelta(minutes=2)})
    assert envelope["artifact_id"] == model.artifact_id
    assert restored_prediction.probabilities == pytest.approx(prediction.probabilities)

    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["model_version"] = "tampered"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ModelArtifactError, match="checksum"):
        load_b3_artifact(path)


def test_b3_artifact_requires_independently_trusted_feature_snapshot_manifest(tmp_path) -> None:
    model = train_b3_model(rows=rows(), schema=SCHEMA, backend="lightgbm", seed=7, created_at=datetime(2026, 1, 20, tzinfo=UTC))
    path = tmp_path / "b3.json"
    model.save_artifact(path)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["training_manifest"]["feature_snapshot_hashes"][-1] = "tampered"
    envelope["training_manifest"]["feature_snapshot_manifest_hash"] = "0" * 64
    payload = {key: value for key, value in envelope.items() if key not in {"artifact_id", "model_version", "artifact_sha256"}}
    import hashlib
    envelope["artifact_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    envelope["artifact_id"] = "b3-" + envelope["artifact_sha256"][:16]
    envelope["model_version"] = "b3-lightgbm-" + envelope["artifact_sha256"][:12]
    path.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(ModelArtifactError, match="feature snapshot manifest"):
        load_b3_artifact(path)


def test_b3_abstains_on_unavailable_inputs_and_catboost_is_a_separate_backend() -> None:
    model = train_b3_model(rows=rows(), schema=SCHEMA, backend="catboost", seed=7, created_at=datetime(2026, 1, 20, tzinfo=UTC))
    prediction = model.predict(race_id="race-3", entry_features={"a": {"recent_form": None, "adjusted_speed": 1.8}, "b": {"recent_form": 0.1, "adjusted_speed": 0.2}}, cutoff=datetime(2026, 1, 25, tzinfo=UTC), eligible_at={"a": datetime(2026, 1, 25, tzinfo=UTC) - timedelta(minutes=2), "b": datetime(2026, 1, 25, tzinfo=UTC) - timedelta(minutes=2)})
    assert prediction.state == "ABSTAIN"
    assert prediction.abstention_reason == "UNAVAILABLE_INPUTS"
    assert prediction.backend == "catboost"


def test_b3_requires_pre_race_eligibility_proof() -> None:
    model = train_b3_model(rows=rows(), schema=SCHEMA, backend="lightgbm", seed=7, created_at=datetime(2026, 1, 20, tzinfo=UTC))
    prediction = model.predict(
        race_id="race-3", entry_features={"a": {"recent_form": 1.0, "adjusted_speed": 1.0}},
        cutoff=datetime(2026, 1, 25, tzinfo=UTC),
    )
    assert prediction.state == "ABSTAIN"
    assert prediction.abstention_reason == "MISSING_PRE_RACE_ELIGIBILITY"


def test_b3_adapts_to_the_existing_benchmark_forecast_contract() -> None:
    model = train_b3_model(rows=rows(), schema=SCHEMA, backend="lightgbm", seed=7, created_at=datetime(2026, 1, 20, tzinfo=UTC))
    cutoff = datetime(2026, 1, 25, tzinfo=UTC)
    race = BenchmarkRace(
        "race-3", "THOROUGHBRED", cutoff, (BenchmarkRunner("a"), BenchmarkRunner("b")),
        {"a": {"recent_form": 2.0, "adjusted_speed": 1.8}, "b": {"recent_form": 0.1, "adjusted_speed": 0.2}}, {},
    )
    forecast = build_b3_forecast(model=model, race=race, eligible_at={"a": cutoff - timedelta(minutes=2), "b": cutoff - timedelta(minutes=2)})
    assert forecast.state == "READY"
    assert sum(forecast.probabilities.values()) == pytest.approx(1.0)
    assert "B3_RACE_NORMALISED" in forecast.diagnostics
