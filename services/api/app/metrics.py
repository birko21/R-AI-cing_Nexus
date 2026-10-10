"""Race-level implementation metrics for synthetic forecast evaluation."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import random
from collections.abc import Mapping, Sequence

from app.probability import categorical_log_loss, multiclass_brier_score


@dataclass(frozen=True)
class EvaluationRecord:
    race_id: str
    code: str
    observed_at: datetime
    horizon: str
    model_version: str
    probabilities: Mapping[str, float]
    winner_entry_id: str
    missingness: tuple[str, ...] = ()
    data_mode: str = "SYNTHETIC_ONLY"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    return value.astimezone(timezone.utc)


def _percentile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot calculate percentile of empty values")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _bootstrap_interval(values: Sequence[float], *, seed: int, repetitions: int) -> tuple[float, float]:
    if repetitions <= 0:
        raise ValueError("bootstrap repetitions must be positive")
    rng = random.Random(seed)
    samples = [sum(rng.choice(values) for _ in values) / len(values) for _ in range(repetitions)]
    return (_percentile(samples, 0.025), _percentile(samples, 0.975))


def _score_records(records: Sequence[EvaluationRecord]) -> tuple[list[float], list[float]]:
    log_losses = [categorical_log_loss(record.probabilities, record.winner_entry_id) for record in records]
    brier_scores = [multiclass_brier_score(record.probabilities, record.winner_entry_id) for record in records]
    return log_losses, brier_scores


def _calibration(records: Sequence[EvaluationRecord], bin_count: int = 5) -> list[dict[str, float | int]]:
    bins: list[list[tuple[float, int]]] = [[] for _ in range(bin_count)]
    for record in records:
        for entry_id, probability in record.probabilities.items():
            index = min(bin_count - 1, int(probability * bin_count))
            bins[index].append((probability, int(entry_id == record.winner_entry_id)))
    output: list[dict[str, float | int]] = []
    for index, values in enumerate(bins):
        if not values:
            continue
        output.append({
            "bin": index,
            "count": len(values),
            "mean_predicted": sum(value[0] for value in values) / len(values),
            "empirical_rate": sum(value[1] for value in values) / len(values),
        })
    return output


def _segment(records: Sequence[EvaluationRecord]) -> dict[str, object]:
    log_losses, brier_scores = _score_records(records)
    timestamps = sorted(_utc(record.observed_at) for record in records)
    missing = Counter(reason for record in records for reason in record.missingness)
    return {
        "n": len(records),
        "log_loss": sum(log_losses) / len(log_losses),
        "brier": sum(brier_scores) / len(brier_scores),
        "time_range": {"start": timestamps[0].isoformat().replace("+00:00", "Z"), "end": timestamps[-1].isoformat().replace("+00:00", "Z")},
        "missingness": dict(sorted(missing.items())),
    }


def evaluate_records(records: Sequence[EvaluationRecord], *, bootstrap_seed: int = 20260115, bootstrap_repetitions: int = 1000) -> dict[str, object]:
    """Evaluate scored races and report implementation-only synthetic metrics."""

    if not records:
        raise ValueError("at least one evaluation record is required")
    if any(record.data_mode != "SYNTHETIC_ONLY" for record in records):
        raise ValueError("RIL-028 metrics are restricted to SYNTHETIC_ONLY records")
    for record in records:
        _utc(record.observed_at)
    log_losses, brier_scores = _score_records(records)
    timestamps = sorted(_utc(record.observed_at) for record in records)
    missing = Counter(reason for record in records for reason in record.missingness)
    code_groups: dict[str, list[EvaluationRecord]] = defaultdict(list)
    for record in records:
        code_groups[record.code].append(record)
    model_versions = sorted({record.model_version for record in records})
    horizons = sorted({record.horizon for record in records})
    return {
        "metric_status": "IMPLEMENTATION_METRICS_SYNTHETIC_ONLY",
        "validated_claim": False,
        "data_mode": "SYNTHETIC_ONLY",
        "n": len(records),
        "time_range": {"start": timestamps[0].isoformat().replace("+00:00", "Z"), "end": timestamps[-1].isoformat().replace("+00:00", "Z")},
        "codes": sorted(code_groups),
        "horizon": horizons[0] if len(horizons) == 1 else "MIXED",
        "model_version": model_versions[0] if len(model_versions) == 1 else "MIXED",
        "log_loss": sum(log_losses) / len(log_losses),
        "brier": sum(brier_scores) / len(brier_scores),
        "confidence_intervals": {
            "log_loss_95": list(_bootstrap_interval(log_losses, seed=bootstrap_seed, repetitions=bootstrap_repetitions)),
            "brier_95": list(_bootstrap_interval(brier_scores, seed=bootstrap_seed + 1, repetitions=bootstrap_repetitions)),
        },
        "calibration": _calibration(records),
        "missingness": dict(sorted(missing.items())),
        "segments": {code: _segment(group) for code, group in sorted(code_groups.items())},
        "conventions": {"log_loss": "mean(-ln(p_winner))", "brier": "mean(sum((p_i-y_i)^2))", "confidence_interval": "deterministic percentile bootstrap 2.5%-97.5%"},
    }
