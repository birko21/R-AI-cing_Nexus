from datetime import datetime, timezone

import pytest

from app.harness_scenarios import HarnessFact, build_harness_scenario


CUTOFF = datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc)


def test_harness_scenario_supports_position_inputs_and_labels_hypotheses_experimental() -> None:
    result = build_harness_scenario(
        scenario_id="scenario-1", participant_id="p1", cutoff=CUTOFF,
        facts=(HarnessFact("p1", datetime(2025, 12, 1, tzinfo=timezone.utc), "receipt-h-1", "MOBILE", 1, 3, "MIDFIELD", 31.2, "settles behind leader"),),
    )
    assert result.status == "EXPERIMENTAL"
    assert result.scenario_label == "EXPERIMENTAL_UNCALIBRATED"
    assert result.inputs["start_type"].value == "MOBILE"
    assert result.inputs["row"].value == 1
    assert result.inputs["barrier"].value == 3
    assert result.inputs["sectional_time"].value == 31.2
    assert result.hypotheses and all(hypothesis.startswith("EXPERIMENTAL_") for hypothesis in result.hypotheses)
    assert result.included_receipt_ids == ("receipt-h-1",)


def test_missing_history_returns_not_available_without_hypotheses() -> None:
    result = build_harness_scenario(scenario_id="scenario-1", participant_id="p1", cutoff=CUTOFF, facts=())
    assert result.status == "NOT_AVAILABLE"
    assert result.hypotheses == ()
    assert all(value.missing_reason == "NO_PRE_CUTOFF_SUPPORT" for value in result.inputs.values())


def test_future_facts_are_excluded_and_invalid_inputs_fail_closed() -> None:
    result = build_harness_scenario(
        scenario_id="scenario-1", participant_id="p1", cutoff=CUTOFF,
        facts=(HarnessFact("p1", datetime(2026, 1, 15, 12, tzinfo=timezone.utc), "future"),),
    )
    assert result.excluded_future_receipt_ids == ("future",)
    with pytest.raises(ValueError, match="timezone-aware"):
        build_harness_scenario(scenario_id="scenario-1", participant_id="p1", cutoff=datetime(2026, 1, 15), facts=())
    with pytest.raises(ValueError, match="data_mode"):
        build_harness_scenario(scenario_id="scenario-1", participant_id="p1", cutoff=CUTOFF, facts=(), data_mode="LICENSED")
