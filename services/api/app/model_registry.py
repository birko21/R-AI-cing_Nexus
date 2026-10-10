"""Immutable model registry with manual assurance and promotion controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from collections.abc import Mapping
import hashlib
import json
from typing import Literal


RegistryStatus = Literal["INSUFFICIENT EVIDENCE", "SHADOW", "HOLD", "BLOCK", "CHAMPION"]
ASSURANCE_OUTCOMES = frozenset({"PENDING", "PASS", "FAIL"})
REGISTRY_STATUSES = frozenset({"INSUFFICIENT EVIDENCE", "SHADOW", "HOLD", "BLOCK", "CHAMPION"})


class RegistryError(ValueError):
    """Raised for invalid registry writes or promotion attempts."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ModelArtifact:
    artifact_id: str
    model_id: str
    model_version: str
    artifact_sha256: str
    feature_schema_version: str
    data_mode: str
    model_status: str
    created_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ModelEvaluation:
    evaluation_id: str
    artifact_id: str
    split_manifest_hash: str
    metrics: dict[str, object]
    sample_count: int
    data_mode: str
    created_at: str
    evaluation_hash: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AssuranceEvent:
    assurance_id: str
    evaluation_id: str
    outcome: str
    reviewer: str
    notes: str
    created_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RegistryDecision:
    decision_id: str
    artifact_id: str
    status: RegistryStatus
    decision_reason: str
    approved_by: str | None
    evaluation_id: str | None
    assurance_id: str | None
    manual_approval: bool
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ModelRegistry:
    def __init__(self) -> None:
        self._artifacts: dict[str, str] = {}
        self._evaluations: dict[str, str] = {}
        self._assurance: dict[str, str] = {}
        self._decisions: dict[str, str] = {}

    def register_artifact(self, artifact: ModelArtifact) -> None:
        payload = _canonical(artifact.to_dict())
        existing = self._artifacts.get(artifact.artifact_id)
        if existing is not None and existing != payload:
            raise RegistryError(f"artifact {artifact.artifact_id} is immutable")
        self._artifacts[artifact.artifact_id] = payload

    def record_evaluation(self, evaluation: ModelEvaluation) -> None:
        if evaluation.artifact_id not in self._artifacts:
            raise RegistryError("evaluation references an unknown artifact")
        payload = _canonical(evaluation.to_dict())
        existing = self._evaluations.get(evaluation.evaluation_id)
        if existing is not None and existing != payload:
            raise RegistryError(f"evaluation {evaluation.evaluation_id} is immutable")
        self._evaluations[evaluation.evaluation_id] = payload

    def record_assurance(self, event: AssuranceEvent) -> None:
        if event.evaluation_id not in self._evaluations:
            raise RegistryError("assurance references an unknown evaluation")
        if event.outcome not in ASSURANCE_OUTCOMES:
            raise RegistryError("assurance outcome is unsupported")
        payload = _canonical(event.to_dict())
        existing = self._assurance.get(event.assurance_id)
        if existing is not None and existing != payload:
            raise RegistryError(f"assurance {event.assurance_id} is immutable")
        self._assurance[event.assurance_id] = payload

    def decide(self, decision: RegistryDecision, *, automated: bool = False) -> None:
        if decision.artifact_id not in self._artifacts:
            raise RegistryError("decision references an unknown artifact")
        if decision.status not in REGISTRY_STATUSES:
            raise RegistryError("registry status is unsupported")
        if automated:
            raise RegistryError("automated model promotion is disabled")
        if decision.status == "CHAMPION":
            if not decision.manual_approval or not decision.approved_by:
                raise RegistryError("CHAMPION requires manual approval")
            if not decision.assurance_id or decision.assurance_id not in self._assurance:
                raise RegistryError("CHAMPION requires independent assurance")
            assurance = json.loads(self._assurance[decision.assurance_id])
            if assurance["outcome"] != "PASS":
                raise RegistryError("CHAMPION requires passing independent assurance")
        payload = _canonical(decision.to_dict())
        existing = self._decisions.get(decision.decision_id)
        if existing is not None and existing != payload:
            raise RegistryError(f"decision {decision.decision_id} is immutable")
        self._decisions[decision.decision_id] = payload

    def leaderboard(self) -> list[dict[str, object]]:
        latest: dict[str, dict[str, object]] = {}
        for decision in (json.loads(value) for value in self._decisions.values()):
            latest[decision["artifact_id"]] = decision
        rows = []
        for artifact_id, raw in self._artifacts.items():
            artifact = json.loads(raw)
            row = {**artifact, "registry_status": latest.get(artifact_id, {}).get("status", "INSUFFICIENT EVIDENCE")}
            rows.append(row)
        return sorted(rows, key=lambda row: (row["registry_status"], row["artifact_id"]))

    def snapshot(self) -> dict[str, object]:
        return {
            "available_statuses": sorted(REGISTRY_STATUSES),
            "automated_promotion": False,
            "artifacts": [json.loads(value) for value in self._artifacts.values()],
            "evaluations": [json.loads(value) for value in self._evaluations.values()],
            "assurance": [json.loads(value) for value in self._assurance.values()],
            "decisions": [json.loads(value) for value in self._decisions.values()],
            "leaderboard": self.leaderboard(),
        }


def evaluation_hash(metrics: Mapping[str, object], split_manifest_hash: str, sample_count: int) -> str:
    return _hash({"metrics": dict(metrics), "split_manifest_hash": split_manifest_hash, "sample_count": sample_count})
