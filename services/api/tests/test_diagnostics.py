from __future__ import annotations

import pytest

from app.diagnostics import DiagnosticConfig, diagnose_forecast


def test_diagnostics_keep_probabilities_separate_from_evidence_strength() -> None:
    probabilities = {"entry-1": 0.7, "entry-2": 0.3}
    result = diagnose_forecast(probabilities, support_count=4, comparison_probabilities={"entry-1": 0.72, "entry-2": 0.28})

    assert result.probabilities == probabilities
    assert result.evidence_strength == "HIGH"
    assert result.coverage == 1.0
    assert result.abstain is False
    assert result.disagreement == pytest.approx(0.02)


def test_missingness_disagreement_and_ood_produce_explicit_warnings_and_abstention() -> None:
    result = diagnose_forecast(
        {"entry-1": 0.7, "entry-2": 0.3}, support_count=3, missingness=["MISSING_SECTIONAL"],
        comparison_probabilities={"entry-1": 0.95, "entry-2": 0.05}, ood_score=0.9,
    )

    assert result.evidence_strength == "LOW"
    assert result.ood_warning is True
    assert result.abstain is True
    assert result.abstention_reasons == ("MISSING_FEATURES", "MODEL_DISAGREEMENT", "OUT_OF_DISTRIBUTION")
    assert result.missingness == ("MISSING_SECTIONAL",)


def test_support_threshold_controls_coverage_and_insufficient_state() -> None:
    result = diagnose_forecast({"entry-1": 1.0}, support_count=1, config=DiagnosticConfig(minimum_support=3))

    assert result.coverage == pytest.approx(1 / 3)
    assert result.evidence_strength == "INSUFFICIENT"
    assert result.abstention_reasons == ("INSUFFICIENT_SUPPORT",)


def test_diagnostics_reject_invalid_ood_or_disagreement_membership() -> None:
    with pytest.raises(ValueError, match="identical field"):
        diagnose_forecast({"entry-1": 1.0}, support_count=2, comparison_probabilities={"entry-2": 1.0})
    with pytest.raises(ValueError, match="ood_score"):
        diagnose_forecast({"entry-1": 1.0}, support_count=2, ood_score=-0.1)

