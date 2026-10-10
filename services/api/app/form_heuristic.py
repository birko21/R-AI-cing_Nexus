"""Explicit, deterministic and illustrative B1 form heuristic."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Literal

from app.baseline import MODEL_STATUS, VALID_FIELD_STATES


MODEL_ID = "B1_FORM_HEURISTIC"
MODEL_VERSION = "b1-form-v1"
MINIMUM_SUPPORT = 2
SMOOTHING = 0.1
ForecastStatus = Literal["READY", "ABSTAIN"]


@dataclass(frozen=True)
class FormRun:
    participant_id: str
    observed_at: datetime
    distance: int | None
    finish_position: int | None


@dataclass(frozen=True)
class FormRunner:
    entry_id: str
    participant_id: str
    number: int
    status: str = "ACTIVE"
    eligible: bool = True
    coupled_group: str | None = None
    runs: tuple[FormRun, ...] = ()


@dataclass(frozen=True)
class FormRace:
    race_id: str
    code: str
    field_revision: str
    field_status: str
    target_distance: int | None
    runners: tuple[FormRunner, ...]
    data_mode: str = "SYNTHETIC_ONLY"


@dataclass(frozen=True)
class FormFeatures:
    support_count: int
    form_score: float
    distance_match: float
    recency_score: float
    raw_score: float
    smoothed_score: float


@dataclass(frozen=True)
class B1RunnerForecast:
    entry_id: str
    number: int
    probability: float | None
    features: FormFeatures | None


@dataclass(frozen=True)
class B1Forecast:
    forecast_id: str
    race_id: str
    code: str
    field_revision: str
    field_status: str
    cutoff: str
    target_distance: int | None
    model_id: str
    model_version: str
    model_status: str
    data_mode: str
    manifest_checksum: str
    weights: dict[str, float]
    smoothing: float
    minimum_support: int
    status: ForecastStatus
    runners: tuple[B1RunnerForecast, ...]
    abstention_reason: str | None
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "runners": [asdict(runner) for runner in self.runners],
            "diagnostics": list(self.diagnostics),
        }


CODE_WEIGHTS: dict[str, dict[str, float]] = {
    "THOROUGHBRED": {"form": 0.55, "distance": 0.30, "recency": 0.15, "half_life_days": 30.0},
    "HARNESS": {"form": 0.50, "distance": 0.35, "recency": 0.15, "half_life_days": 45.0},
    "GREYHOUND": {"form": 0.45, "distance": 0.20, "recency": 0.35, "half_life_days": 21.0},
}


def _normalise_cutoff(cutoff: datetime) -> str:
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("cutoff must be timezone-aware")
    return cutoff.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _forecast_id(race: FormRace, cutoff: str, checksum: str) -> str:
    payload = json.dumps(
        {
            "race_id": race.race_id,
            "field_revision": race.field_revision,
            "cutoff": cutoff,
            "target_distance": race.target_distance,
            "model_id": MODEL_ID,
            "model_version": MODEL_VERSION,
            "manifest_checksum": checksum,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"b1-{hashlib.sha256(payload).hexdigest()[:16]}"


def _abstain(race: FormRace, *, cutoff: str, checksum: str, reason: str, diagnostics: tuple[str, ...] = ()) -> B1Forecast:
    weights = CODE_WEIGHTS.get(race.code, {})
    return B1Forecast(
        forecast_id=_forecast_id(race, cutoff, checksum), race_id=race.race_id, code=race.code,
        field_revision=race.field_revision, field_status=race.field_status, cutoff=cutoff,
        target_distance=race.target_distance, model_id=MODEL_ID, model_version=MODEL_VERSION,
        model_status=MODEL_STATUS, data_mode=race.data_mode, manifest_checksum=checksum,
        weights=weights, smoothing=SMOOTHING, minimum_support=MINIMUM_SUPPORT, status="ABSTAIN",
        runners=tuple(), abstention_reason=reason, diagnostics=diagnostics,
    )


def _distance_match(run_distance: int, target_distance: int) -> float:
    delta = abs(run_distance - target_distance)
    return 1.0 if delta == 0 else 0.5 if delta <= 200 else 0.0


def build_b1_forecast(race: FormRace, *, cutoff: datetime, manifest_checksum: str) -> B1Forecast:
    """Produce normalized B1 probabilities from strictly pre-cutoff form.

    Missing or insufficient form abstains for the whole race; it never silently
    substitutes B0 or a fabricated feature value.
    """

    if not manifest_checksum:
        raise ValueError("manifest_checksum is required")
    cutoff_text = _normalise_cutoff(cutoff)
    weights = CODE_WEIGHTS.get(race.code)
    if weights is None:
        return _abstain(race, cutoff=cutoff_text, checksum=manifest_checksum, reason="UNSUPPORTED_CODE")
    if race.data_mode != "SYNTHETIC_ONLY":
        return _abstain(race, cutoff=cutoff_text, checksum=manifest_checksum, reason="UNSUPPORTED_DATA_MODE")
    if race.target_distance is None or race.target_distance <= 0:
        return _abstain(race, cutoff=cutoff_text, checksum=manifest_checksum, reason="MISSING_TARGET_DISTANCE")
    if race.field_status not in VALID_FIELD_STATES:
        return _abstain(race, cutoff=cutoff_text, checksum=manifest_checksum, reason="FIELD_NOT_VALID")
    if not race.runners:
        return _abstain(race, cutoff=cutoff_text, checksum=manifest_checksum, reason="INCOMPLETE_FIELD")
    if any(runner.coupled_group for runner in race.runners):
        return _abstain(race, cutoff=cutoff_text, checksum=manifest_checksum, reason="COUPLED_ENTRY")
    active = tuple(runner for runner in race.runners if runner.status == "ACTIVE" and runner.eligible)
    if not active:
        return _abstain(race, cutoff=cutoff_text, checksum=manifest_checksum, reason="NO_ACTIVE_ELIGIBLE_RUNNERS")

    feature_rows: list[tuple[FormRunner, FormFeatures]] = []
    for runner in active:
        pre_cutoff = tuple(run for run in runner.runs if run.observed_at < cutoff)
        usable = tuple(run for run in pre_cutoff if run.distance is not None and run.distance > 0 and run.finish_position is not None and run.finish_position > 0)
        if len(usable) < MINIMUM_SUPPORT:
            return _abstain(
                race, cutoff=cutoff_text, checksum=manifest_checksum, reason="INSUFFICIENT_SUPPORT",
                diagnostics=(f"{runner.entry_id}:support={len(usable)}",),
            )
        form_score = sum(1.0 / run.finish_position for run in usable) / len(usable)
        distance_score = sum(_distance_match(run.distance, race.target_distance) for run in usable) / len(usable)
        recency_score = sum(
            math.exp(-max(0.0, (cutoff - run.observed_at).total_seconds() / 86400.0) / weights["half_life_days"])
            for run in usable
        ) / len(usable)
        raw_score = weights["form"] * form_score + weights["distance"] * distance_score + weights["recency"] * recency_score
        smoothed_score = raw_score + SMOOTHING
        if not all(math.isfinite(value) for value in (form_score, distance_score, recency_score, raw_score, smoothed_score)):
            return _abstain(race, cutoff=cutoff_text, checksum=manifest_checksum, reason="NONFINITE_FEATURE")
        feature_rows.append((runner, FormFeatures(len(usable), form_score, distance_score, recency_score, raw_score, smoothed_score)))

    total_score = sum(features.smoothed_score for _, features in feature_rows)
    if not math.isfinite(total_score) or total_score <= 0:
        return _abstain(race, cutoff=cutoff_text, checksum=manifest_checksum, reason="NONFINITE_NORMALIZER")
    forecasts = tuple(
        B1RunnerForecast(runner.entry_id, runner.number, features.smoothed_score / total_score, features)
        for runner, features in feature_rows
    )
    return B1Forecast(
        forecast_id=_forecast_id(race, cutoff_text, manifest_checksum), race_id=race.race_id, code=race.code,
        field_revision=race.field_revision, field_status=race.field_status, cutoff=cutoff_text,
        target_distance=race.target_distance, model_id=MODEL_ID, model_version=MODEL_VERSION,
        model_status=MODEL_STATUS, data_mode=race.data_mode, manifest_checksum=manifest_checksum,
        weights=weights, smoothing=SMOOTHING, minimum_support=MINIMUM_SUPPORT, status="READY",
        runners=forecasts, abstention_reason=None,
        diagnostics=("PRE_CUTOFF_RUNS_ONLY", f"MINIMUM_SUPPORT={MINIMUM_SUPPORT}", "NORMALIZED_PROBABILITIES"),
    )
