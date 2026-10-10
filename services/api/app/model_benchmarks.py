"""Offline B0-B4 benchmark contracts with explicit abstention semantics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
from typing import Literal

from app.probability import validate_probabilities


MODEL_STATUS = "ILLUSTRATIVE_NOT_VALIDATED"
ForecastState = Literal["READY", "ABSTAIN"]
RunnerStatus = Literal["ACTIVE", "SCRATCHED", "RESERVE"]


@dataclass(frozen=True)
class BenchmarkRunner:
    entry_id: str
    status: RunnerStatus = "ACTIVE"
    eligible: bool = True
    coupled_group: str | None = None


@dataclass(frozen=True)
class MarketInput:
    back_price: float | None
    lay_price: float | None
    source_timestamp: datetime
    available_back_volume: float | None = None
    available_lay_volume: float | None = None
    matched_volume: float | None = None

    def __post_init__(self) -> None:
        if self.source_timestamp.tzinfo is None or self.source_timestamp.utcoffset() is None:
            raise ValueError("market source timestamp must be timezone-aware")
        for name, value in (("back_price", self.back_price), ("lay_price", self.lay_price)):
            if value is not None and (not math.isfinite(value) or value < 1):
                raise ValueError(f"{name} must be decimal odds >= 1")
        for name, value in (("available_back_volume", self.available_back_volume), ("available_lay_volume", self.available_lay_volume), ("matched_volume", self.matched_volume)):
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True)
class BenchmarkRace:
    race_id: str
    code: str
    cutoff: datetime
    runners: tuple[BenchmarkRunner, ...]
    form_features: dict[str, dict[str, float | None]]
    market_inputs: dict[str, MarketInput]
    data_mode: str = "SYNTHETIC_ONLY"


@dataclass(frozen=True)
class BenchmarkForecast:
    model_id: str
    model_version: str
    race_id: str
    code: str
    cutoff: str
    state: ForecastState
    probabilities: dict[str, float]
    model_status: str
    missingness: tuple[str, ...]
    diagnostics: tuple[str, ...]
    overround: float | None = None
    spread_used: bool = False
    abstention_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


B1_WEIGHTS: dict[str, dict[str, float]] = {
    "THOROUGHBRED": {"historical_performance": 0.25, "recent_form": 0.2, "distance_suitability": 0.15, "adjusted_speed": 0.2, "race_class": 0.1, "fitness": 0.1},
    "HARNESS": {"historical_performance": 0.2, "recent_form": 0.2, "distance_suitability": 0.15, "adjusted_speed": 0.2, "driver_effect": 0.1, "fitness": 0.15},
    "GREYHOUND": {"historical_performance": 0.2, "recent_form": 0.2, "distance_suitability": 0.1, "adjusted_speed": 0.2, "early_speed": 0.15, "box": 0.15},
}


def _cutoff_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("benchmark cutoff must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _eligible(race: BenchmarkRace) -> tuple[BenchmarkRunner, ...]:
    if not race.runners:
        return tuple()
    if any(runner.coupled_group for runner in race.runners):
        return tuple()
    return tuple(runner for runner in race.runners if runner.status == "ACTIVE" and runner.eligible)


def _abstain(race: BenchmarkRace, model_id: str, model_version: str, reason: str, missingness: tuple[str, ...] = ()) -> BenchmarkForecast:
    return BenchmarkForecast(model_id, model_version, race.race_id, race.code, _cutoff_text(race.cutoff), "ABSTAIN", {}, MODEL_STATUS, missingness, (), abstention_reason=reason)


def _ready(race: BenchmarkRace, model_id: str, model_version: str, probabilities: dict[str, float], *, missingness: tuple[str, ...] = (), diagnostics: tuple[str, ...] = (), overround: float | None = None, spread_used: bool = False) -> BenchmarkForecast:
    validate_probabilities(probabilities, [runner.entry_id for runner in _eligible(race)])
    return BenchmarkForecast(model_id, model_version, race.race_id, race.code, _cutoff_text(race.cutoff), "READY", probabilities, MODEL_STATUS, missingness, diagnostics, overround, spread_used)


def build_b0_forecast(race: BenchmarkRace) -> BenchmarkForecast:
    active = _eligible(race)
    if not active:
        return _abstain(race, "B0_UNIFORM", "b0-uniform-v2", "INCOMPLETE_OR_COUPLED_FIELD")
    probability = 1 / len(active)
    return _ready(race, "B0_UNIFORM", "b0-uniform-v2", {runner.entry_id: probability for runner in active}, diagnostics=("EQUAL_ACTIVE_ELIGIBLE_RUNNERS",))


def build_b1_form_forecast(race: BenchmarkRace) -> BenchmarkForecast:
    active = _eligible(race)
    if not active:
        return _abstain(race, "B1_FORM_BASELINE", "b1-form-v2", "INCOMPLETE_OR_COUPLED_FIELD")
    weights = B1_WEIGHTS.get(race.code)
    if weights is None:
        return _abstain(race, "B1_FORM_BASELINE", "b1-form-v2", "UNSUPPORTED_CODE")
    scores: dict[str, float] = {}
    missing: list[str] = []
    for runner in active:
        features = race.form_features.get(runner.entry_id, {})
        usable = [(name, value) for name, weight in weights.items() if (value := features.get(name)) is not None and math.isfinite(value) and weight > 0]
        if not usable:
            missing.append(f"{runner.entry_id}:NO_FORM_SUPPORT")
            continue
        total_weight = sum(weights[name] for name, _ in usable)
        scores[runner.entry_id] = sum(weights[name] * value for name, value in usable) / total_weight
        missing.extend(f"{runner.entry_id}:MISSING_{name}" for name in weights if features.get(name) is None)
    if len(scores) != len(active):
        return _abstain(race, "B1_FORM_BASELINE", "b1-form-v2", "INSUFFICIENT_FORM_SUPPORT", tuple(sorted(set(missing))))
    maximum = max(scores.values())
    exp_scores = {entry_id: math.exp(score - maximum) for entry_id, score in scores.items()}
    normalizer = math.fsum(exp_scores.values())
    return _ready(race, "B1_FORM_BASELINE", "b1-form-v2", {entry_id: value / normalizer for entry_id, value in exp_scores.items()}, missingness=tuple(sorted(set(missing))), diagnostics=("CODE_SPECIFIC_WEIGHTED_FORM", "NO_IMPUTATION"))


def build_b2_market_forecast(race: BenchmarkRace) -> BenchmarkForecast:
    active = _eligible(race)
    if not active:
        return _abstain(race, "B2_MARKET_BASELINE", "b2-market-v1", "INCOMPLETE_OR_COUPLED_FIELD")
    implied: dict[str, float] = {}
    missing: list[str] = []
    spread_used = False
    for runner in active:
        quote = race.market_inputs.get(runner.entry_id)
        if quote is None:
            missing.append(f"{runner.entry_id}:MISSING_MARKET")
            continue
        if quote.source_timestamp > race.cutoff:
            missing.append(f"{runner.entry_id}:FUTURE_MARKET_TIMESTAMP")
            continue
        if quote.back_price is not None and quote.lay_price is not None:
            price = (quote.back_price + quote.lay_price) / 2
            spread_used = True
        elif quote.back_price is not None:
            price = quote.back_price
        else:
            missing.append(f"{runner.entry_id}:MISSING_BACK_PRICE")
            continue
        implied[runner.entry_id] = 1 / price
    if len(implied) != len(active):
        return _abstain(race, "B2_MARKET_BASELINE", "b2-market-v1", "INCOMPLETE_MARKET", tuple(sorted(set(missing))))
    overround = math.fsum(implied.values())
    probabilities = {entry_id: value / overround for entry_id, value in implied.items()}
    return _ready(race, "B2_MARKET_BASELINE", "b2-market-v1", probabilities, missingness=tuple(sorted(set(missing))), diagnostics=("OVERROUND_NORMALISED", "EXCHANGE_SPREAD_MIDPOINT" if spread_used else "BACK_PRICE_ONLY"), overround=overround, spread_used=spread_used)


def build_b4_market_informed_ensemble(race: BenchmarkRace, *, form_weight: float = 0.5) -> BenchmarkForecast:
    if not 0 <= form_weight <= 1:
        raise ValueError("form_weight must be between 0 and 1")
    form = build_b1_form_forecast(race)
    market = build_b2_market_forecast(race)
    if form.state != "READY" or market.state != "READY":
        return _abstain(race, "B4_MARKET_INFORMED_ENSEMBLE", "b4-ensemble-v1", "FORM_OR_MARKET_UNAVAILABLE", tuple(sorted(set(form.missingness + market.missingness))))
    combined = {
        entry_id: math.exp(form_weight * math.log(form.probabilities[entry_id]) + (1 - form_weight) * math.log(market.probabilities[entry_id]))
        for entry_id in form.probabilities
    }
    normalizer = math.fsum(combined.values())
    return _ready(race, "B4_MARKET_INFORMED_ENSEMBLE", "b4-ensemble-v1", {entry_id: value / normalizer for entry_id, value in combined.items()}, diagnostics=("LOG_LINEAR_FORM_MARKET_COMBINATION", "CALIBRATION_REQUIRED_BEFORE_PROMOTION"), spread_used=market.spread_used)


class MachineLearningBackendUnavailable(RuntimeError):
    """Raised when the optional LightGBM/CatBoost dependency is absent."""


def build_b3_lightgbm_or_catboost(*, backend: Literal["lightgbm", "catboost"] = "lightgbm") -> None:
    """Fail closed until an approved, reproducible ML engine is installed."""

    try:
        __import__(backend)
    except ImportError as exc:
        raise MachineLearningBackendUnavailable(f"{backend} is not installed; B3 is NOT_AVAILABLE") from exc
