from datetime import datetime, timezone

import pytest

from app.challenger_study import BASELINES, ModelScore, StudySpec, compare_challenger


START = datetime(2025, 12, 1, tzinfo=timezone.utc)
END = datetime(2026, 1, 1, tzinfo=timezone.utc)


def spec() -> StudySpec:
    return StudySpec(study_id="study-1", preregistered_at=datetime(2025, 11, 1, tzinfo=timezone.utc), holdout_start=START, holdout_end=END, challenger_id="TB_CHALLENGER_V1", metric="BRIER", data_mode="SYNTHETIC_ONLY")


def scores(challenger: float = 0.20) -> tuple[ModelScore, ...]:
    values = {"B0_UNIFORM": 0.30, "B1_FORM_HEURISTIC": 0.28, "MARKET_BASELINE": 0.25, "TB_CHALLENGER_V1": challenger}
    return tuple(ModelScore(model_id=model_id, holdout_start=START, holdout_end=END, sample_size=100, metric_value=value, ci_low=value - 0.02, ci_high=value + 0.02) for model_id, value in values.items())


def test_challenger_comparison_is_chronological_and_preregistered() -> None:
    report = compare_challenger(spec(), scores())
    assert report.status == "COMPLETE"
    assert set(report.ranking) == BASELINES | {"TB_CHALLENGER_V1"}
    assert report.promotion.status == "HOLD"
    assert report.synthetic_only is True


def test_no_champion_without_independent_assurance_and_owner_approval() -> None:
    held = compare_challenger(spec(), scores(), independent_assurance=True)
    assert held.promotion.status == "HOLD"
    approved = compare_challenger(spec(), scores(), independent_assurance=True, owner_approval=True)
    assert approved.promotion.status == "CHAMPION"


def test_missing_baseline_and_holdout_mismatch_fail_closed() -> None:
    missing = tuple(score for score in scores() if score.model_id != "MARKET_BASELINE")
    with pytest.raises(ValueError, match="missing required"):
        compare_challenger(spec(), missing)
    mismatched = list(scores())
    mismatched[0] = mismatched[0].model_copy(update={"holdout_end": datetime(2026, 1, 2, tzinfo=timezone.utc)})
    with pytest.raises(ValueError, match="preregistered"):
        compare_challenger(spec(), tuple(mismatched))
