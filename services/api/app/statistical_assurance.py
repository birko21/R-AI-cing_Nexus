"""Independent statistical assurance primitives for chronological research.

These utilities intentionally do not fetch data or promote models.  They make
the train/calibration/test boundaries, race-level calibration, ablation
retraining and the independent conditional-choice challenger inspectable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from collections.abc import Callable, Mapping, Sequence

from app.ml_models import FeatureSchema, TrainingRow, _hash
from app.walk_forward import WalkForwardFold


def _normalise(values: Mapping[str, float]) -> dict[str, float]:
    if not values or any(not math.isfinite(value) or value < 0 for value in values.values()):
        raise ValueError("probabilities must be finite and non-negative")
    total = math.fsum(values.values())
    if total <= 0:
        raise ValueError("probabilities must contain positive mass")
    return {key: value / total for key, value in values.items()}


@dataclass(frozen=True)
class FoldAssuranceRecord:
    fold_id: str
    training_race_ids: tuple[str, ...]
    calibration_race_ids: tuple[str, ...]
    test_race_ids: tuple[str, ...]
    training_cutoff: str
    validation_window: tuple[str, str]
    test_window: tuple[str, str]
    dataset_hash: str
    training_feature_snapshot_hashes: tuple[str, ...]
    model_artifact_id: str
    calibration_artifact_id: str
    test_artifact_id: str
    record_hash: str

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        for key in ("training_race_ids", "calibration_race_ids", "test_race_ids", "training_feature_snapshot_hashes"):
            value[key] = list(value[key])
        value["validation_window"] = list(self.validation_window)
        value["test_window"] = list(self.test_window)
        return value


def make_fold_assurance_record(
    fold: WalkForwardFold,
    *,
    dataset_hash: str,
    training_feature_snapshot_hashes: Sequence[str],
    model_artifact_id: str,
    calibration_artifact_id: str,
    test_artifact_id: str,
) -> FoldAssuranceRecord:
    if not dataset_hash or any(not value for value in training_feature_snapshot_hashes):
        raise ValueError("dataset and feature snapshot hashes are required")
    if set(fold.training_race_ids) & set(fold.calibration_race_ids) or set(fold.training_race_ids) & set(fold.test_race_ids) or set(fold.calibration_race_ids) & set(fold.test_race_ids):
        raise ValueError("fold race memberships overlap")
    body = {
        "fold_id": fold.fold_id,
        "training_race_ids": fold.training_race_ids,
        "calibration_race_ids": fold.calibration_race_ids,
        "test_race_ids": fold.test_race_ids,
        "training_cutoff": fold.training_end,
        "validation_window": [fold.calibration_start, fold.calibration_end],
        "test_window": [fold.test_start, fold.test_end],
        "dataset_hash": dataset_hash,
        "training_feature_snapshot_hashes": tuple(sorted(training_feature_snapshot_hashes)),
        "model_artifact_id": model_artifact_id,
        "calibration_artifact_id": calibration_artifact_id,
        "test_artifact_id": test_artifact_id,
    }
    return FoldAssuranceRecord(**body, record_hash=_hash(body))


class RaceTemperatureCalibrator:
    """Race-level temperature scaling fitted only on a held-out calibration set."""

    def __init__(self, temperature: float, calibration_race_ids: tuple[str, ...], artifact_id: str):
        if temperature <= 0 or not calibration_race_ids:
            raise ValueError("calibration requires a positive temperature and races")
        self.temperature = temperature
        self.calibration_race_ids = calibration_race_ids
        self.artifact_id = artifact_id

    @staticmethod
    def _loss(samples: Sequence[tuple[Mapping[str, float], str]], temperature: float) -> float:
        total = 0.0
        for probabilities, winner in samples:
            normalised = _normalise(probabilities)
            weights = {entry: math.exp(math.log(max(probability, 1e-15)) / temperature) for entry, probability in normalised.items()}
            total += -math.log(weights[winner] / math.fsum(weights.values()))
        return total / len(samples)

    @classmethod
    def fit(cls, samples: Sequence[tuple[str, Mapping[str, float], str]]) -> "RaceTemperatureCalibrator":
        if not samples or len({race_id for race_id, _, _ in samples}) != len(samples):
            raise ValueError("calibration requires one unique sample per race")
        compact = [(probabilities, winner) for _, probabilities, winner in samples]
        candidates = [0.25 + index * 0.05 for index in range(76)]
        temperature = min(candidates, key=lambda value: (cls._loss(compact, value), value))
        race_ids = tuple(sorted(race_id for race_id, _, _ in samples))
        artifact_id = "calibration-" + _hash({"temperature": temperature, "race_ids": race_ids})[:16]
        return cls(temperature, race_ids, artifact_id)

    def apply(self, probabilities: Mapping[str, float]) -> dict[str, float]:
        normalised = _normalise(probabilities)
        scores = {entry: math.exp(math.log(max(probability, 1e-15)) / self.temperature) for entry, probability in normalised.items()}
        total = math.fsum(scores.values())
        return {entry: score / total for entry, score in scores.items()}

    def to_dict(self) -> dict[str, object]:
        return {"artifact_id": self.artifact_id, "temperature": self.temperature, "calibration_race_ids": list(self.calibration_race_ids), "status": "HELD_OUT_RACE_LEVEL_CALIBRATION"}


@dataclass(frozen=True)
class AblationResult:
    removed_feature_family: str
    retained_feature_names: tuple[str, ...]
    schema_hash: str
    retrained_model_artifact_id: str
    training_row_count: int


def ablate_and_retrain(
    rows: Sequence[TrainingRow],
    schema: FeatureSchema,
    *,
    feature_family_by_name: Mapping[str, str],
    removed_feature_family: str,
    trainer: Callable[[tuple[TrainingRow, ...], FeatureSchema], str],
) -> AblationResult:
    retained = tuple(name for name in schema.feature_names if feature_family_by_name.get(name) != removed_feature_family)
    if not retained:
        raise ValueError("ablation cannot remove every feature")
    ablated_schema = FeatureSchema(schema.code, schema.family, retained, schema.schema_version + f"-without-{removed_feature_family}")
    ablated_rows = tuple(TrainingRow(
        row.race_id, row.entry_id, row.code, row.family, row.cutoff, row.pre_race_eligible_at,
        {name: row.feature_values[name] for name in retained}, row.winner, row.data_mode,
        row.source_receipt_ids, ablated_schema.schema_hash,
    ) for row in rows)
    artifact_id = trainer(ablated_rows, ablated_schema)
    return AblationResult(removed_feature_family, retained, ablated_schema.schema_hash, artifact_id, len(ablated_rows))


@dataclass(frozen=True)
class ChoiceModel:
    """Small race-level conditional-logit challenger, independent of B3."""

    feature_names: tuple[str, ...]
    weights: tuple[float, ...]
    schema_hash: str
    model_id: str

    @classmethod
    def fit(cls, rows: Sequence[TrainingRow], schema: FeatureSchema, *, epochs: int = 300, learning_rate: float = 0.05) -> "ChoiceModel":
        if not rows:
            raise ValueError("choice model requires rows")
        if any(row.feature_schema_hash != schema.schema_hash for row in rows):
            raise ValueError("choice rows do not match schema")
        groups: dict[str, list[TrainingRow]] = {}
        for row in rows:
            groups.setdefault(row.race_id, []).append(row)
        if any(sum(row.winner for row in group) != 1 for group in groups.values()):
            raise ValueError("each choice race must have one winner")
        weights = [0.0] * len(schema.feature_names)
        for _ in range(epochs):
            gradient = [0.0] * len(weights)
            for group in groups.values():
                scores = [sum(weights[index] * (row.feature_values[name] or 0.0) for index, name in enumerate(schema.feature_names)) for row in group]
                scale = max(scores)
                exp_scores = [math.exp(score - scale) for score in scores]
                total = math.fsum(exp_scores)
                for index, name in enumerate(schema.feature_names):
                    expected = sum((exp_scores[pos] / total) * (group[pos].feature_values[name] or 0.0) for pos in range(len(group)))
                    actual = next((row.feature_values[name] or 0.0 for row in group if row.winner), 0.0)
                    gradient[index] += actual - expected
            weights = [weight + learning_rate * gradient[index] / len(groups) for index, weight in enumerate(weights)]
        model_id = "choice-" + _hash({"schema_hash": schema.schema_hash, "weights": weights})[:16]
        return cls(schema.feature_names, tuple(weights), schema.schema_hash, model_id)

    def predict(self, entry_features: Mapping[str, Mapping[str, float]]) -> dict[str, float]:
        if any(tuple(features) != self.feature_names for features in entry_features.values()):
            raise ValueError("choice feature schema mismatch")
        scores = {entry: sum(self.weights[index] * values[name] for index, name in enumerate(self.feature_names)) for entry, values in entry_features.items()}
        scale = max(scores.values())
        masses = {entry: math.exp(score - scale) for entry, score in scores.items()}
        total = math.fsum(masses.values())
        return {entry: mass / total for entry, mass in masses.items()}
