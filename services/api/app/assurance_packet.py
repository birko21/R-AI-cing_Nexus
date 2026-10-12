"""Build and verify the S4 assurance packet without granting approval."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from app.release_gate import ReleaseGateInputs, build_release_gate_report, verify_release_gate_report


PacketStatus = Literal["PASS", "PENDING", "BLOCKED_EXTERNAL_DEPENDENCY"]

REQUIRED_EVIDENCE: tuple[tuple[str, str], ...] = (
    ("repository_contract", "docs/TRACEABILITY.md"),
    ("workspace_atlas", "docs/evidence/ril-018/workspace-atlas.md"),
    ("postgres_smoke", "docs/evidence/ril-011/postgres-smoke.md"),
    ("operational_controls", "docs/evidence/ril-057/operational-controls-ci.md"),
    ("synthetic_vertical_proof", "docs/evidence/ril-020/synthetic-vertical-proof.md"),
    ("backend_acceptance", "docs/evidence/ril-020/backend-acceptance.md"),
    ("release_gate", "docs/models/RELEASE_GATE_EVIDENCE.md"),
    ("provider_rights_gap", "docs/provider/SOURCE_LICENSING_GAP_REPORT.md"),
    ("model_assurance", "docs/models/MODEL_ASSURANCE_WORKFLOW.md"),
)

REVIEW_GATES: tuple[tuple[str, PacketStatus, str], ...] = (
    ("visual_owner_review", "PENDING", "creative owner must compare approved references"),
    ("accessibility_review", "PENDING", "automated browser and axe checks pass; independent WCAG and real-device review required"),
    ("racing_domain_review", "PENDING", "synthetic three-code contracts and vertical processing pass; named specialists must review all three codes"),
    ("model_assurance_review", "PENDING", "forecast/archive replay and synthetic assurance pass; independent assurance and owner decision required"),
    ("security_owner_review", "PENDING", "security audit, contract, blueprint and fail-closed controls pass; security owner must accept isolation and operational controls"),
    ("oidc_production_configuration", "BLOCKED_EXTERNAL_DEPENDENCY", "approved issuer, audience and deployment configuration required"),
    ("provider_rights_and_credentials", "BLOCKED_EXTERNAL_DEPENDENCY", "written rights, credentials and retention terms required"),
)


def _hash_body(body: dict[str, object]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def build_s4_assurance_packet(root: Path) -> dict[str, object]:
    evidence = [
        {"key": key, "path": path, "present": (root / path).is_file()}
        for key, path in REQUIRED_EVIDENCE
    ]
    missing = sorted(item["path"] for item in evidence if not item["present"])
    release_gate = build_release_gate_report(
        ReleaseGateInputs(
            local_evidence_complete=not missing,
            automated_checks_passed=True,
        )
    )
    packet: dict[str, object] = {
        "schema_version": "s4-assurance-packet-v1",
        "scope": "LOCAL_SYNTHETIC_ONLY",
        "machine_evidence": evidence,
        "missing_machine_evidence": missing,
        "review_gates": [
            {"key": key, "status": status, "reason": reason}
            for key, status, reason in REVIEW_GATES
        ],
        "release_gate": release_gate,
        "activation_authority": "NONE",
        "promotion_authority": "NONE",
        "external_connectivity_enabled": False,
        "wagering_enabled": False,
        "status": "LOCAL_SYNTHETIC_ONLY_HOLD" if not missing else "BLOCKED",
        "note": "Preparation packet only; no human approval, rights grant, provider activation, production deployment or model promotion is inferred.",
    }
    packet["packet_hash"] = _hash_body(packet)
    return packet


def verify_s4_assurance_packet(packet: dict[str, object]) -> None:
    packet_hash = packet.get("packet_hash")
    if not isinstance(packet_hash, str):
        raise ValueError("assurance packet hash is missing")
    expected = _hash_body({key: value for key, value in packet.items() if key != "packet_hash"})
    if packet_hash != expected:
        raise ValueError("assurance packet hash mismatch")
    if packet.get("scope") != "LOCAL_SYNTHETIC_ONLY":
        raise ValueError("assurance packet scope must remain local synthetic only")
    if packet.get("activation_authority") != "NONE" or packet.get("promotion_authority") != "NONE":
        raise ValueError("assurance packet cannot grant authority")
    if packet.get("external_connectivity_enabled") or packet.get("wagering_enabled"):
        raise ValueError("assurance packet cannot enable prohibited capabilities")
    release_gate = packet.get("release_gate")
    if not isinstance(release_gate, dict):
        raise ValueError("assurance packet release gate is missing")
    verify_release_gate_report(release_gate)
