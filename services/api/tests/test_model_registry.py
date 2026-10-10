from __future__ import annotations

import pytest

from app.model_registry import (
    AssuranceEvent,
    ModelArtifact,
    ModelEvaluation,
    ModelRegistry,
    RegistryDecision,
    RegistryError,
    evaluation_hash,
)


def artifact(artifact_id: str = "b1-v1") -> ModelArtifact:
    return ModelArtifact(artifact_id, "B1_FORM_HEURISTIC", "b1-form-v1", "a" * 64, "features-v1", "SYNTHETIC_ONLY", "ILLUSTRATIVE_NOT_VALIDATED", "2026-01-15T00:00:00Z")


def evaluation(artifact_id: str = "b1-v1") -> ModelEvaluation:
    metrics = {"n": 3, "log_loss": 1.0, "brier": 0.4}
    return ModelEvaluation("eval-1", artifact_id, "b" * 64, metrics, 3, "SYNTHETIC_ONLY", "2026-01-15T00:00:00Z", evaluation_hash(metrics, "b" * 64, 3))


def decision(decision_id: str, status: str, artifact_id: str = "b1-v1", **kwargs: object) -> RegistryDecision:
    return RegistryDecision(decision_id, artifact_id, status, "Recorded for restricted pilot review", kwargs.get("approved_by"), kwargs.get("evaluation_id"), kwargs.get("assurance_id"), bool(kwargs.get("manual_approval", False)), "2026-01-15T00:00:00Z")


def test_registry_retains_immutable_artifacts_evaluations_and_rejected_models() -> None:
    registry = ModelRegistry()
    registry.register_artifact(artifact())
    registry.record_evaluation(evaluation())
    registry.decide(decision("decision-block", "BLOCK"))
    registry.register_artifact(artifact("b0-v1"))
    registry.decide(decision("decision-shadow", "SHADOW", "b0-v1"))

    assert len(registry.snapshot()["artifacts"]) == 2
    assert {row["registry_status"] for row in registry.leaderboard()} == {"BLOCK", "SHADOW"}
    with pytest.raises(RegistryError, match="artifact .* immutable"):
        registry.register_artifact(artifact().__class__("b1-v1", "B1_FORM_HEURISTIC", "changed", "c" * 64, "features-v1", "SYNTHETIC_ONLY", "ILLUSTRATIVE_NOT_VALIDATED", "2026-01-15T00:00:00Z"))


def test_registry_exposes_hold_and_insufficient_evidence_without_promotion() -> None:
    registry = ModelRegistry()
    registry.register_artifact(artifact())
    registry.decide(decision("decision-insufficient", "INSUFFICIENT EVIDENCE"))
    registry.decide(decision("decision-hold", "HOLD"))

    assert "INSUFFICIENT EVIDENCE" in registry.snapshot()["available_statuses"]
    assert {row["registry_status"] for row in registry.leaderboard()} == {"HOLD"}


def test_automated_promotion_and_unassured_champion_are_blocked() -> None:
    registry = ModelRegistry()
    registry.register_artifact(artifact())
    registry.record_evaluation(evaluation())

    with pytest.raises(RegistryError, match="automated model promotion"):
        registry.decide(decision("auto", "CHAMPION", evaluation_id="eval-1", approved_by="owner", manual_approval=True), automated=True)
    with pytest.raises(RegistryError, match="independent assurance"):
        registry.decide(decision("champion-no-assurance", "CHAMPION", evaluation_id="eval-1", approved_by="owner", manual_approval=True))


def test_champion_requires_passing_independent_assurance_and_manual_approval() -> None:
    registry = ModelRegistry()
    registry.register_artifact(artifact())
    registry.record_evaluation(evaluation())
    registry.record_assurance(AssuranceEvent("assurance-1", "eval-1", "PASS", "independent-reviewer", "Reproduced synthetic evaluation.", "2026-01-16T00:00:00Z"))
    registry.decide(decision("champion", "CHAMPION", evaluation_id="eval-1", assurance_id="assurance-1", approved_by="owner", manual_approval=True))

    assert registry.leaderboard()[0]["registry_status"] == "CHAMPION"

