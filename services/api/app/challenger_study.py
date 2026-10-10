"""Preregistered synthetic challenger comparison and promotion gate."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


BASELINES = frozenset({"B0_UNIFORM", "B1_FORM_HEURISTIC", "MARKET_BASELINE"})
StudyStatus = Literal["COMPLETE", "INVALID"]
PromotionStatus = Literal["HOLD", "CHAMPION"]


class StudySpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    study_id: str = Field(min_length=1)
    preregistered_at: datetime
    holdout_start: datetime
    holdout_end: datetime
    challenger_id: str = Field(min_length=1)
    metric: Literal["LOG_LOSS", "BRIER"]
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]

    @model_validator(mode="after")
    def validate_dates(self) -> StudySpec:
        if any(value.tzinfo is None or value.utcoffset() is None for value in (self.preregistered_at, self.holdout_start, self.holdout_end)):
            raise ValueError("study timestamps must be timezone-aware")
        if self.holdout_end <= self.holdout_start:
            raise ValueError("holdout_end must be after holdout_start")
        return self


class ModelScore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    model_id: str = Field(min_length=1)
    holdout_start: datetime
    holdout_end: datetime
    sample_size: int = Field(ge=1)
    metric_value: float = Field(ge=0)
    ci_low: float = Field(ge=0)
    ci_high: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_interval(self) -> ModelScore:
        if self.holdout_end <= self.holdout_start or self.ci_low > self.ci_high:
            raise ValueError("invalid chronological holdout or confidence interval")
        return self


class PromotionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: PromotionStatus
    independent_assurance: bool
    owner_approval: bool
    reason: str


class StudyReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    study_id: str
    status: StudyStatus
    metric: str
    scores: tuple[ModelScore, ...]
    ranking: tuple[str, ...]
    promotion: PromotionDecision
    synthetic_only: Literal[True] = True


def compare_challenger(spec: StudySpec, scores: tuple[ModelScore, ...], *, independent_assurance: bool = False, owner_approval: bool = False) -> StudyReport:
    expected = BASELINES | {spec.challenger_id}
    by_model = {score.model_id: score for score in scores}
    missing = expected - set(by_model)
    if missing:
        raise ValueError(f"missing required comparison models: {sorted(missing)}")
    for score in scores:
        if score.holdout_start != spec.holdout_start or score.holdout_end != spec.holdout_end:
            raise ValueError("all scores must use the preregistered chronological holdout")
    ranking = tuple(model_id for model_id, _ in sorted(by_model.items(), key=lambda item: (item[1].metric_value, item[0])))
    challenger = by_model[spec.challenger_id]
    best_baseline = min(by_model[model_id].metric_value for model_id in BASELINES)
    promoted = independent_assurance and owner_approval and challenger.metric_value < best_baseline
    promotion = PromotionDecision(
        status="CHAMPION" if promoted else "HOLD", independent_assurance=independent_assurance,
        owner_approval=owner_approval,
        reason="challenger beat every baseline with required approvals" if promoted else "no champion without independent assurance and owner approval",
    )
    return StudyReport(
        study_id=spec.study_id, status="COMPLETE", metric=spec.metric, scores=scores,
        ranking=ranking, promotion=promotion,
    )
