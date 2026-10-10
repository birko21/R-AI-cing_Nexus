from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.model_registry import ModelArtifact, ModelEvaluation, ModelRegistry, RegistryDecision, evaluation_hash  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "model_registry_v1.json"


def build_fixture() -> dict[str, object]:
    registry = ModelRegistry()
    artifacts = [
        ModelArtifact("b0-v1", "B0_UNIFORM", "b0-uniform-v1", "0" * 64, "features-v1", "SYNTHETIC_ONLY", "ILLUSTRATIVE_NOT_VALIDATED", "2026-01-15T00:00:00Z"),
        ModelArtifact("b1-v1", "B1_FORM_HEURISTIC", "b1-form-v1", "1" * 64, "features-v1", "SYNTHETIC_ONLY", "ILLUSTRATIVE_NOT_VALIDATED", "2026-01-15T00:00:00Z"),
        ModelArtifact("insufficient-v0", "EXPERIMENTAL_FORM", "exp-v0", "2" * 64, "features-v1", "SYNTHETIC_ONLY", "EXPERIMENTAL", "2026-01-15T00:00:00Z"),
        ModelArtifact("rejected-v0", "EXPERIMENTAL_FORM", "exp-v0-rejected", "3" * 64, "features-v1", "SYNTHETIC_ONLY", "EXPERIMENTAL", "2026-01-15T00:00:00Z"),
    ]
    for artifact in artifacts:
        registry.register_artifact(artifact)
    for artifact_id in ("b0-v1", "b1-v1"):
        metrics = {"n": 3, "log_loss": 1.0, "brier": 0.4}
        registry.record_evaluation(ModelEvaluation(f"eval-{artifact_id}", artifact_id, "4" * 64, metrics, 3, "SYNTHETIC_ONLY", "2026-01-15T00:00:00Z", evaluation_hash(metrics, "4" * 64, 3)))
    registry.decide(RegistryDecision("decision-b0", "b0-v1", "SHADOW", "Baseline retained for comparison.", None, "eval-b0-v1", None, False, "2026-01-15T00:00:00Z"))
    registry.decide(RegistryDecision("decision-b1", "b1-v1", "HOLD", "Insufficient independent evidence for promotion.", None, "eval-b1-v1", None, False, "2026-01-15T00:00:00Z"))
    registry.decide(RegistryDecision("decision-insufficient", "insufficient-v0", "INSUFFICIENT EVIDENCE", "Support threshold not met.", None, None, None, False, "2026-01-15T00:00:00Z"))
    registry.decide(RegistryDecision("decision-rejected", "rejected-v0", "BLOCK", "Failed reproducibility review; retained for audit.", None, None, None, False, "2026-01-15T00:00:00Z"))
    snapshot = registry.snapshot()
    snapshot.update({
        "schema_version": "model-registry-v1",
        "current_champion": None,
        "automated_promotion": False,
        "promotion_policy": "CHAMPION requires passing independent assurance and explicit manual approval.",
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
    })
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("REGISTRY FIXTURE CHECK FAILED: generated content differs")
    print(f"REGISTRY FIXTURE VALID: artifacts={len(expected['artifacts'])} champion={expected['current_champion']}")


if __name__ == "__main__":
    main()
