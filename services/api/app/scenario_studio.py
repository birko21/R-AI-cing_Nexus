"""Reproducible synthetic scenario simulation with calibration abstention."""

from __future__ import annotations

import hashlib
import json
import random
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ScenarioStatus = Literal["SIMULATED", "ABSTAIN"]
CalibrationStatus = Literal["CALIBRATED", "ABSENT"]


class ScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: str = Field(min_length=1)
    seed: int = Field(ge=0)
    sample_size: int = Field(ge=1, le=5000)
    assumptions: tuple[str, ...] = Field(min_length=1)
    observed_fact_ids: tuple[str, ...] = ()
    hypotheses: tuple[str, ...] = ()
    inputs: dict[str, float] = Field(default_factory=dict)
    model_version: str = Field(min_length=1)
    calibration_status: CalibrationStatus
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]

    @model_validator(mode="after")
    def validate_labels(self) -> ScenarioRequest:
        if any(not value.strip() for value in (*self.assumptions, *self.observed_fact_ids, *self.hypotheses)):
            raise ValueError("scenario labels must contain non-empty values")
        if any(not 0 <= value <= 1 for value in self.inputs.values()):
            raise ValueError("scenario inputs must be bounded between 0 and 1")
        if self.calibration_status == "ABSENT" and self.hypotheses == ():
            raise ValueError("uncalibrated scenarios must state a hypothesis or abstain rationale")
        return self


class ScenarioResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: str
    status: ScenarioStatus
    seed: int
    sample_size: int
    assumptions: tuple[str, ...]
    observed_fact_ids: tuple[str, ...]
    hypotheses: tuple[str, ...]
    model_version: str
    data_mode: str
    outputs: tuple[float, ...]
    abstention_reason: str | None
    output_hash: str


def run_scenario(request: ScenarioRequest) -> ScenarioResult:
    outputs: tuple[float, ...]
    status: ScenarioStatus
    abstention_reason: str | None
    if request.calibration_status == "ABSENT":
        outputs = ()
        status = "ABSTAIN"
        abstention_reason = "CALIBRATION_ABSENT"
    else:
        rng = random.Random(request.seed)
        outputs = tuple(round(rng.random(), 12) for _ in range(request.sample_size))
        status = "SIMULATED"
        abstention_reason = None
    body = {
        "scenario_id": request.scenario_id, "status": status, "seed": request.seed,
        "sample_size": request.sample_size, "assumptions": list(request.assumptions),
        "observed_fact_ids": list(request.observed_fact_ids), "hypotheses": list(request.hypotheses),
        "inputs": request.inputs, "model_version": request.model_version, "data_mode": request.data_mode,
        "outputs": list(outputs), "abstention_reason": abstention_reason,
    }
    output_hash = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return ScenarioResult(
        scenario_id=request.scenario_id, status=status, seed=request.seed, sample_size=request.sample_size,
        assumptions=request.assumptions, observed_fact_ids=request.observed_fact_ids, hypotheses=request.hypotheses,
        model_version=request.model_version, data_mode=request.data_mode, outputs=outputs,
        abstention_reason=abstention_reason, output_hash=output_hash,
    )
