"""Fail-closed B3 LightGBM/CatBoost training and inference lifecycle.

The model wrapper is deliberately independent of provider adapters. It accepts
only versioned, rights-aware feature rows and emits race-normalised forecasts.
Artifacts are JSON envelopes containing a backend-native text/JSON model, not
pickle files, so loading is deterministic and inspectable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import base64
import hashlib
import json
import math
from pathlib import Path
import tempfile
from typing import Literal, Mapping


Backend = Literal["lightgbm", "catboost"]
ModelFamily = Literal["FORM_ONLY", "MARKET_ONLY", "COMBINED"]
MODEL_STATUS = "ILLUSTRATIVE_NOT_VALIDATED"
ALLOWED_DATA_MODES = frozenset({"SYNTHETIC_ONLY", "APPROVED"})


class MLBackendUnavailable(RuntimeError):
    """Raised when the requested optional ML backend cannot be imported."""


class ModelArtifactError(ValueError):
    """Raised for invalid, tampered or incompatible model artifacts."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class FeatureSchema:
    code: str
    family: ModelFamily
    feature_names: tuple[str, ...]
    schema_version: str = "b3-feature-schema-v1"

    def __post_init__(self) -> None:
        if not self.code or not self.feature_names or len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("feature schema must contain unique feature names")

    @property
    def schema_hash(self) -> str:
        return _hash(asdict(self))

    def to_dict(self) -> dict[str, object]:
        return {**asdict(self), "feature_names": list(self.feature_names), "schema_hash": self.schema_hash}


@dataclass(frozen=True)
class TrainingRow:
    race_id: str
    entry_id: str
    code: str
    family: ModelFamily
    cutoff: datetime
    pre_race_eligible_at: datetime
    feature_values: Mapping[str, float | None]
    winner: bool
    data_mode: str
    source_receipt_ids: tuple[str, ...]
    feature_schema_hash: str
    feature_snapshot_hash: str | None = None

    def __post_init__(self) -> None:
        cutoff = _timestamp(self.cutoff)
        eligible = _timestamp(self.pre_race_eligible_at)
        if self.pre_race_eligible_at >= self.cutoff:
            raise ValueError("training row is not pre-race eligible")
        if self.data_mode not in ALLOWED_DATA_MODES:
            raise ValueError("training row data mode is not approved")
        if not self.race_id or not self.entry_id or not self.feature_schema_hash:
            raise ValueError("training row identifiers and schema hash are required")
        if not cutoff or not eligible:
            raise ValueError("training row timestamps are required")
        for value in self.feature_values.values():
            if value is not None and not math.isfinite(value):
                raise ValueError("training feature values must be finite or null")
        expected = _hash({
            "race_id": self.race_id,
            "entry_id": self.entry_id,
            "code": self.code,
            "family": self.family,
            "cutoff": cutoff,
            "pre_race_eligible_at": eligible,
            "feature_values": dict(sorted(self.feature_values.items())),
            "winner": self.winner,
            "data_mode": self.data_mode,
            "source_receipt_ids": list(self.source_receipt_ids),
            "feature_schema_hash": self.feature_schema_hash,
        })
        if self.feature_snapshot_hash is not None and self.feature_snapshot_hash != expected:
            raise ValueError("training feature snapshot hash does not match complete row")
        object.__setattr__(self, "feature_snapshot_hash", expected)


@dataclass(frozen=True)
class TrainingManifest:
    manifest_version: str
    backend: Backend
    code: str
    family: ModelFamily
    seed: int
    data_mode: str
    feature_schema_hash: str
    row_count: int
    race_count: int
    training_row_hash: str
    created_at: str
    dependency_version: str
    feature_snapshot_hashes: tuple[str, ...] = ()
    feature_snapshot_manifest_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["feature_snapshot_hashes"] = list(self.feature_snapshot_hashes)
        return payload

    def verify_feature_snapshot_manifest(self) -> None:
        expected = _hash(list(self.feature_snapshot_hashes))
        if self.feature_snapshot_manifest_hash != expected:
            raise ModelArtifactError("feature snapshot manifest hash mismatch")


@dataclass(frozen=True)
class B3Prediction:
    state: Literal["READY", "ABSTAIN"]
    probabilities: dict[str, float]
    model_id: str
    model_version: str
    artifact_id: str
    backend: Backend
    model_status: str
    feature_schema_hash: str
    training_manifest_hash: str
    missingness: tuple[str, ...] = ()
    abstention_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _load_backend(backend: Backend):
    try:
        if backend == "lightgbm":
            import lightgbm as module
        else:
            import catboost as module
    except ImportError as exc:
        raise MLBackendUnavailable(f"{backend} is not installed") from exc
    return module


def _fit_model(backend: Backend, x: list[list[float]], y: list[int], seed: int):
    module = _load_backend(backend)
    if backend == "lightgbm":
        import numpy as np

        dataset = module.Dataset(np.asarray(x, dtype=float), label=np.asarray(y, dtype=int), free_raw_data=False)
        model = module.train(
            {"objective": "binary", "learning_rate": 0.05, "num_leaves": 7,
             "min_data_in_leaf": 1, "min_data_in_bin": 1, "seed": seed,
             "verbosity": -1, "num_threads": 1},
            dataset, num_boost_round=32,
        )
    else:
        model = module.CatBoostClassifier(
            iterations=32, depth=4, learning_rate=0.05, loss_function="Logloss",
            random_seed=seed, verbose=False, allow_writing_files=False,
        )
        model.fit(x, y)
    return model, module


def _model_text(backend: Backend, model: object) -> str:
    if backend == "lightgbm":
        return model.model_to_string()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
        path = Path(handle.name)
    try:
        model.save_model(str(path), format="json")
        return path.read_text(encoding="utf-8")
    finally:
        path.unlink(missing_ok=True)


def _restore_model(backend: Backend, model_text: str):
    module = _load_backend(backend)
    if backend == "lightgbm":
        return module.Booster(model_str=model_text)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as handle:
        handle.write(model_text)
        path = Path(handle.name)
    try:
        model = module.CatBoostClassifier()
        model.load_model(str(path), format="json")
        return model
    finally:
        path.unlink(missing_ok=True)


def _prediction_scores(model: object, rows: list[list[float]]) -> list[float]:
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(rows)
        scores = [float(row[1]) for row in probabilities]
    else:
        scores = [float(value) for value in model.predict(rows)]
    if not scores or any(not math.isfinite(value) or value < 0 for value in scores):
        raise ModelArtifactError("backend returned invalid winning scores")
    total = math.fsum(scores)
    if total <= 0:
        raise ModelArtifactError("backend returned no winning mass")
    return [value / total for value in scores]


@dataclass
class TrainedB3Model:
    model_id: str
    model_version: str
    artifact_id: str
    backend: Backend
    schema: FeatureSchema
    seed: int
    data_mode: str
    training_manifest: TrainingManifest
    model: object
    model_text: str

    @property
    def training_manifest_hash(self) -> str:
        return _hash(self.training_manifest.to_dict())

    def predict(self, *, race_id: str, entry_features: Mapping[str, Mapping[str, float | None]], cutoff: datetime, eligible_at: Mapping[str, datetime] | None = None, data_mode: str = "SYNTHETIC_ONLY", allow_missing: bool = False) -> B3Prediction:
        _timestamp(cutoff)
        if not entry_features:
            return self._abstain("EMPTY_FIELD")
        if data_mode != self.data_mode:
            return self._abstain("DATA_MODE_MISMATCH")
        if eligible_at is None or set(eligible_at) != set(entry_features):
            return self._abstain("MISSING_PRE_RACE_ELIGIBILITY")
        try:
            if any(_timestamp(value) and value >= cutoff for value in eligible_at.values()):
                return self._abstain("POST_CUTOFF_FEATURES")
        except ValueError:
            return self._abstain("INVALID_PRE_RACE_ELIGIBILITY")
        if any(set(features) != set(self.schema.feature_names) for features in entry_features.values()):
            return self._abstain("FEATURE_SCHEMA_MISMATCH")
        missing = tuple(sorted(f"{entry}:{name}" for entry, features in entry_features.items() for name, value in features.items() if value is None))
        if missing and not allow_missing:
            return self._abstain("UNAVAILABLE_INPUTS", missing)
        rows = [[math.nan if features[name] is None else float(features[name]) for name in self.schema.feature_names] for features in entry_features.values()]
        probabilities = _prediction_scores(self.model, rows)
        return B3Prediction(
            "READY", dict(zip(entry_features, probabilities)), self.model_id, self.model_version,
            self.artifact_id, self.backend, MODEL_STATUS, self.schema.schema_hash,
            self.training_manifest_hash, missing,
        )

    def _abstain(self, reason: str, missingness: tuple[str, ...] = ()) -> B3Prediction:
        return B3Prediction(
            "ABSTAIN", {}, self.model_id, self.model_version, self.artifact_id, self.backend,
            MODEL_STATUS, self.schema.schema_hash, self.training_manifest_hash, missingness, reason,
        )

    def save_artifact(self, path: Path) -> dict[str, object]:
        payload = {
            "artifact_version": "b3-artifact-v1", "model_id": self.model_id,
            "backend": self.backend,
            "seed": self.seed, "data_mode": self.data_mode, "model_status": MODEL_STATUS,
            "schema": self.schema.to_dict(), "training_manifest": self.training_manifest.to_dict(),
            "model_text_b64": base64.b64encode(self.model_text.encode("utf-8")).decode("ascii"),
        }
        artifact_sha = _hash(payload)
        envelope = {**payload, "artifact_id": self.artifact_id, "model_version": self.model_version, "artifact_sha256": artifact_sha}
        if self.artifact_id != f"b3-{artifact_sha[:16]}" or self.model_version != f"b3-{self.backend}-{artifact_sha[:12]}":
            raise ModelArtifactError("model artifact identity is inconsistent")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return envelope


def build_b3_forecast(*, model: TrainedB3Model, race: object, eligible_at: Mapping[str, datetime]):
    """Adapt a trained B3 model to the existing ``BenchmarkForecast`` contract."""

    from app.model_benchmarks import BenchmarkForecast

    if model.schema.code != race.code:
        return BenchmarkForecast(
            model.model_id, model.model_version, race.race_id, race.code, _timestamp(race.cutoff),
            "ABSTAIN", {}, MODEL_STATUS, (), ("MODEL_CODE_MISMATCH",), abstention_reason="MODEL_CODE_MISMATCH",
        )
    active = tuple(runner for runner in race.runners if runner.status == "ACTIVE" and runner.eligible and not runner.coupled_group)
    if not active or len(active) != len(tuple(runner for runner in race.runners if runner.status == "ACTIVE" and runner.eligible)):
        return BenchmarkForecast(
            model.model_id, model.model_version, race.race_id, race.code, _timestamp(race.cutoff),
            "ABSTAIN", {}, MODEL_STATUS, (), ("INCOMPLETE_OR_COUPLED_FIELD",), abstention_reason="INCOMPLETE_OR_COUPLED_FIELD",
        )
    entry_features: dict[str, dict[str, float | None]] = {}
    for runner in active:
        values = dict(race.form_features.get(runner.entry_id, {}))
        quote = race.market_inputs.get(runner.entry_id)
        if quote is not None:
            midpoint = ((quote.back_price + quote.lay_price) / 2) if quote.back_price is not None and quote.lay_price is not None else quote.back_price
            values.update({
                "pre_race_price": midpoint, "price_movement": 0.0,
                "price_spread": (quote.lay_price - quote.back_price) if quote.back_price is not None and quote.lay_price is not None else None,
                "available_back_volume": quote.available_back_volume, "available_lay_volume": quote.available_lay_volume,
                "matched_volume": quote.matched_volume, "market_depth": 1.0, "market_state": 1.0,
            })
        entry_features[runner.entry_id] = {name: values.get(name) for name in model.schema.feature_names}
    prediction = model.predict(race_id=race.race_id, entry_features=entry_features, cutoff=race.cutoff, eligible_at=eligible_at, data_mode=race.data_mode)
    return BenchmarkForecast(
        model.model_id, model.model_version, race.race_id, race.code, _timestamp(race.cutoff), prediction.state,
        prediction.probabilities, prediction.model_status, prediction.missingness,
        ("B3_RACE_NORMALISED", "CALIBRATION_REQUIRED_BEFORE_PROMOTION"), abstention_reason=prediction.abstention_reason,
    )


def train_b3_model(*, rows: tuple[TrainingRow, ...], schema: FeatureSchema, backend: Backend, seed: int, created_at: datetime) -> TrainedB3Model:
    if not rows:
        raise ValueError("at least one training row is required")
    if backend not in {"lightgbm", "catboost"}:
        raise ValueError("unsupported B3 backend")
    keys = {(row.race_id, row.entry_id) for row in rows}
    if len(keys) != len(rows):
        raise ValueError("duplicate training runner records are not allowed")
    if any(row.code != schema.code or row.family != schema.family or row.feature_schema_hash != schema.schema_hash for row in rows):
        raise ValueError("training rows do not match the feature schema")
    modes = {row.data_mode for row in rows}
    if len(modes) != 1:
        raise ValueError("training rows must use one data mode")
    by_race: dict[str, list[TrainingRow]] = {}
    for row in rows:
        by_race.setdefault(row.race_id, []).append(row)
    if any(sum(row.winner for row in race_rows) != 1 for race_rows in by_race.values()):
        raise ValueError("each training race must have exactly one winner")
    feature_rows = [[math.nan if row.feature_values[name] is None else float(row.feature_values[name]) for name in schema.feature_names] for row in rows]
    targets = [int(row.winner) for row in rows]
    model, module = _fit_model(backend, feature_rows, targets, seed)
    dependency_version = str(getattr(module, "__version__", "UNKNOWN"))
    snapshot_hashes = tuple(sorted(row.feature_snapshot_hash or "" for row in rows))
    row_hash = _hash([{
        "race_id": row.race_id, "entry_id": row.entry_id, "cutoff": _timestamp(row.cutoff),
        "pre_race_eligible_at": _timestamp(row.pre_race_eligible_at), "winner": row.winner,
        "source_receipt_ids": list(row.source_receipt_ids),
        "feature_values": dict(sorted(row.feature_values.items())),
        "feature_snapshot_hash": row.feature_snapshot_hash,
    } for row in sorted(rows, key=lambda value: (value.race_id, value.entry_id))])
    manifest = TrainingManifest(
        "b3-training-manifest-v1", backend, schema.code, schema.family, seed, next(iter(modes)),
        schema.schema_hash, len(rows), len(by_race), row_hash, _timestamp(created_at), dependency_version,
        snapshot_hashes, _hash(list(snapshot_hashes)),
    )
    model_text = _model_text(backend, model)
    artifact_sha = _hash({
        "artifact_version": "b3-artifact-v1", "model_id": f"B3_{schema.code}_{schema.family}",
        "backend": backend, "seed": seed, "data_mode": next(iter(modes)), "model_status": MODEL_STATUS,
        "schema": schema.to_dict(), "training_manifest": manifest.to_dict(),
        "model_text_b64": base64.b64encode(model_text.encode("utf-8")).decode("ascii"),
    })
    return TrainedB3Model(
        f"B3_{schema.code}_{schema.family}", f"b3-{backend}-{artifact_sha[:12]}", f"b3-{artifact_sha[:16]}",
        backend, schema, seed, next(iter(modes)), manifest, model, model_text,
    )


def load_b3_artifact(path: Path, *, trusted_manifest: TrainingManifest | None = None) -> TrainedB3Model:
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
        artifact_sha = envelope["artifact_sha256"]
        artifact_id = envelope["artifact_id"]
        checksum_payload = {key: value for key, value in envelope.items() if key not in {"artifact_id", "model_version", "artifact_sha256"}}
        expected = _hash(checksum_payload)
        if artifact_sha != expected or artifact_id != f"b3-{expected[:16]}" or envelope.get("model_version") != f"b3-{envelope.get('backend')}-{expected[:12]}":
            raise ModelArtifactError("artifact checksum or ID mismatch")
        schema_data = envelope["schema"]
        schema = FeatureSchema(schema_data["code"], schema_data["family"], tuple(schema_data["feature_names"]), schema_data["schema_version"])
        if schema_data.get("schema_hash") != schema.schema_hash:
            raise ModelArtifactError("feature schema hash mismatch")
        manifest = TrainingManifest(**envelope["training_manifest"])
        if manifest.feature_schema_hash != schema.schema_hash:
            raise ModelArtifactError("training manifest schema mismatch")
        manifest.verify_feature_snapshot_manifest()
        if trusted_manifest is not None:
            trusted_manifest.verify_feature_snapshot_manifest()
            if manifest.to_dict() != trusted_manifest.to_dict():
                raise ModelArtifactError("artifact training manifest is not the independently trusted manifest")
        backend = envelope["backend"]
        model = _restore_model(backend, base64.b64decode(envelope["model_text_b64"]).decode("utf-8"))
        return TrainedB3Model(envelope["model_id"], envelope["model_version"], artifact_id, backend, schema, int(envelope["seed"]), envelope["data_mode"], manifest, model, base64.b64decode(envelope["model_text_b64"]).decode("utf-8"))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        if isinstance(exc, ModelArtifactError):
            raise
        raise ModelArtifactError("invalid B3 model artifact") from exc
