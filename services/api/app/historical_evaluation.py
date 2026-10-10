"""Walk-forward evaluation with exclusions, segments and ablation evidence."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.metrics import EvaluationRecord, evaluate_records
from app.probability import validate_probabilities


OutcomeStatus = Literal["SINGLE_WINNER", "DEAD_HEAT", "SCRATCHED", "ABANDONED", "COUPLED_ENTRY"]


@dataclass(frozen=True)
class ForecastCase:
    race_id: str
    code: str
    observed_at: datetime
    model_id: str
    model_version: str
    probabilities: dict[str, float]
    winner_entry_id: str | None
    outcome_status: OutcomeStatus
    track: str | None = None
    distance: int | None = None
    race_type: str | None = None
    feature_family: str | None = None
    missingness: tuple[str, ...] = ()
    market_probabilities: dict[str, float] | None = None
    fold_id: str | None = None
    fold_role: Literal["TRAIN", "CALIBRATION", "TEST"] | None = None
    data_mode: str = "SYNTHETIC_ONLY"

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("forecast observed_at must be timezone-aware")


def _group_summary(cases: list[ForecastCase]) -> dict[str, object]:
    if not cases:
        return {"n": 0, "status": "INSUFFICIENT_HISTORY"}
    report = evaluate_records([
        EvaluationRecord(case.race_id, case.code, case.observed_at, "PRE_RACE", case.model_version, case.probabilities, case.winner_entry_id or "", case.missingness, case.data_mode)
        for case in cases
    ], bootstrap_repetitions=200)
    top_hits = sum(max(case.probabilities, key=case.probabilities.get) == case.winner_entry_id for case in cases)
    return {
        "status": "ILLUSTRATIVE_SYNTHETIC_ONLY",
        "n": len(cases),
        "log_loss": report["log_loss"],
        "brier": report["brier"],
        "calibration": report["calibration"],
        "confidence_intervals": report["confidence_intervals"],
        "top_ranked_win_accuracy": top_hits / len(cases),
        "missing_case_count": sum(bool(case.missingness) for case in cases),
    }


def _accepted_cases(cases: tuple[ForecastCase, ...]) -> tuple[list[ForecastCase], list[dict[str, str]]]:
    accepted: list[ForecastCase] = []
    excluded: list[dict[str, str]] = []
    for case in cases:
        if case.data_mode != "SYNTHETIC_ONLY":
            raise ValueError("historical evaluation is offline synthetic-only until rights are approved")
        if case.outcome_status != "SINGLE_WINNER":
            excluded.append({"race_id": case.race_id, "reason": case.outcome_status})
            continue
        if case.winner_entry_id is None:
            excluded.append({"race_id": case.race_id, "reason": "MISSING_WINNER"})
            continue
        try:
            validate_probabilities(case.probabilities, case.probabilities.keys())
        except ValueError:
            excluded.append({"race_id": case.race_id, "reason": "INVALID_PROBABILITIES"})
            continue
        if case.winner_entry_id not in case.probabilities:
            excluded.append({"race_id": case.race_id, "reason": "WINNER_NOT_IN_FORECAST_FIELD"})
            continue
        if case.fold_role is not None and case.fold_role != "TEST":
            excluded.append({"race_id": case.race_id, "reason": "NON_TEST_CASE"})
            continue
        accepted.append(case)
    return accepted, excluded


def _market_comparison(cases: list[ForecastCase]) -> dict[str, object]:
    comparable = [case for case in cases if case.market_probabilities is not None]
    if not comparable:
        return {"status": "NOT_AVAILABLE", "reason": "NO_CONTEMPORANEOUS_MARKET_PROBABILITIES"}
    for case in comparable:
        validate_probabilities(case.market_probabilities or {}, case.probabilities.keys())
    market_cases = [
        EvaluationRecord(case.race_id, case.code, case.observed_at, "PRE_RACE", "market-implied", case.market_probabilities or {}, case.winner_entry_id or "", case.missingness, case.data_mode)
        for case in comparable
    ]
    report = evaluate_records(market_cases, bootstrap_repetitions=200)
    performance = _group_summary(comparable)
    return {
        "status": "ILLUSTRATIVE_SYNTHETIC_ONLY",
        "n": len(comparable),
        "market_log_loss": report["log_loss"],
        "market_brier": report["brier"],
        "model_log_loss": performance["log_loss"],
        "model_brier": performance["brier"],
        "log_loss_delta_model_minus_market": performance["log_loss"] - report["log_loss"],
        "brier_delta_model_minus_market": performance["brier"] - report["brier"],
    }


def evaluate_forecasts(cases: tuple[ForecastCase, ...]) -> dict[str, object]:
    """Evaluate only valid single-winner test cases and make all exclusions visible."""

    if not cases:
        raise ValueError("at least one forecast case is required")
    accepted, excluded = _accepted_cases(cases)
    by_model: dict[str, list[ForecastCase]] = defaultdict(list)
    by_segment: dict[str, list[ForecastCase]] = defaultdict(list)
    by_missingness: dict[str, list[ForecastCase]] = defaultdict(list)
    for case in accepted:
        by_model[case.model_id].append(case)
        by_segment[f"code={case.code}"].append(case)
        by_segment[f"track={case.track or 'UNKNOWN'}"].append(case)
        by_segment[f"distance={case.distance or 'UNKNOWN'}"].append(case)
        by_segment[f"race_type={case.race_type or 'UNKNOWN'}"].append(case)
        by_missingness["MISSING_INPUTS" if case.missingness else "COMPLETE_INPUTS"].append(case)
    model_reports = {model_id: _group_summary(group) for model_id, group in sorted(by_model.items())}
    ablation = {
        model_id: {"feature_family": next((case.feature_family for case in group if case.feature_family), None), **report}
        for model_id, (group, report) in sorted(((model_id, (group, _group_summary(group))) for model_id, group in by_model.items()))
    }
    folds = sorted({case.fold_id for case in accepted if case.fold_id})
    race_folds: dict[str, set[str]] = defaultdict(set)
    for case in accepted:
        if case.fold_id:
            race_folds[case.race_id].add(case.fold_id)
    duplicate_fold_races = any(len(fold_ids) != 1 for fold_ids in race_folds.values())
    return {
        "report_version": "historical-evaluation-v1",
        "status": "ILLUSTRATIVE_SYNTHETIC_ONLY" if accepted else "INSUFFICIENT_HISTORY",
        "validated_claim": False,
        "input_case_count": len(cases),
        "scored_case_count": len(accepted),
        "excluded_cases": excluded,
        "models": model_reports,
        "feature_family_ablation": ablation,
        "segments": {key: _group_summary(value) for key, value in sorted(by_segment.items())},
        "missing_input_sensitivity": {key: _group_summary(value) for key, value in sorted(by_missingness.items())},
        "market_comparison": {model_id: _market_comparison(group) for model_id, group in sorted(by_model.items())},
        "walk_forward": {"status": "READY" if folds and not duplicate_fold_races else "INCOMPLETE", "test_fold_ids": folds, "duplicate_fold_races": duplicate_fold_races},
    }
