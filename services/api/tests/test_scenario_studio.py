import pytest
from pydantic import ValidationError

from app.scenario_studio import ScenarioRequest, run_scenario


def request(**overrides: object) -> ScenarioRequest:
    payload: dict[str, object] = {
        "scenario_id": "scenario-1", "seed": 42, "sample_size": 25,
        "assumptions": ("Synthetic field is complete",), "observed_fact_ids": ("receipt-1",),
        "hypotheses": ("Experimental pace scenario",), "inputs": {"pace": 0.6},
        "model_version": "scenario-v1", "calibration_status": "CALIBRATED", "data_mode": "SYNTHETIC_ONLY",
    }
    payload.update(overrides)
    return ScenarioRequest.model_validate(payload)


def test_seed_replay_is_deterministic_and_preserves_fact_hypothesis_separation() -> None:
    first = run_scenario(request())
    second = run_scenario(request())
    assert first.status == "SIMULATED"
    assert first.outputs == second.outputs
    assert first.output_hash == second.output_hash
    assert first.observed_fact_ids == ("receipt-1",)
    assert first.hypotheses == ("Experimental pace scenario",)
    assert all(0 <= output <= 1 for output in first.outputs)


def test_uncalibrated_scenario_abstains_without_outputs() -> None:
    result = run_scenario(request(calibration_status="ABSENT"))
    assert result.status == "ABSTAIN"
    assert result.outputs == ()
    assert result.abstention_reason == "CALIBRATION_ABSENT"


def test_sample_bounds_inputs_and_uncalibrated_label_are_enforced() -> None:
    with pytest.raises(ValidationError):
        request(sample_size=5001)
    with pytest.raises(ValidationError, match="bounded"):
        request(inputs={"pace": 1.1})
    with pytest.raises(ValidationError, match="hypothesis"):
        request(calibration_status="ABSENT", hypotheses=())
