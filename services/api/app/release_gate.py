"""Fail-closed aggregation of synthetic release evidence and external gates."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal


GateCheck = Literal["PASS", "PENDING", "BLOCKED_EXTERNAL_DEPENDENCY", "FAIL"]
ReleaseGateStatus = Literal["LOCAL_SYNTHETIC_ONLY_HOLD", "READY_FOR_LOCAL_PILOT", "BLOCKED"]


@dataclass(frozen=True)
class ReleaseGateInputs:
    local_evidence_complete: bool
    automated_checks_passed: bool
    owner_approval: bool = False
    visual_review_complete: bool = False
    accessibility_review_complete: bool = False
    model_assurance_complete: bool = False
    approved_oidc: bool = False
    real_source_rights_approved: bool = False
    external_connectivity_enabled: bool = False
    wagering_enabled: bool = False


def _check(value: bool, *, external: bool = False) -> GateCheck:
    return "PASS" if value else "BLOCKED_EXTERNAL_DEPENDENCY" if external else "PENDING"


def build_release_gate_report(inputs: ReleaseGateInputs) -> dict[str, object]:
    """Build a report without granting approval, activation, or promotion authority."""

    checks: dict[str, GateCheck] = {
        "local_evidence": _check(inputs.local_evidence_complete),
        "automated_validation": _check(inputs.automated_checks_passed),
        "owner_approval": _check(inputs.owner_approval),
        "visual_review": _check(inputs.visual_review_complete),
        "accessibility_review": _check(inputs.accessibility_review_complete),
        "model_assurance": _check(inputs.model_assurance_complete),
        "approved_oidc": _check(inputs.approved_oidc, external=True),
        "real_source_rights": _check(inputs.real_source_rights_approved, external=True),
    }
    blockers = [name for name, status in checks.items() if status in {"PENDING", "FAIL"} and name not in {"approved_oidc", "real_source_rights"}]
    external_gates = [name for name, status in checks.items() if status == "BLOCKED_EXTERNAL_DEPENDENCY"]
    safety_violations = []
    if inputs.external_connectivity_enabled:
        safety_violations.append("external_connectivity_must_remain_disabled")
    if inputs.wagering_enabled:
        safety_violations.append("wagering_must_remain_disabled")
    if safety_violations or any(status == "FAIL" for status in checks.values()) or not inputs.local_evidence_complete or not inputs.automated_checks_passed:
        status: ReleaseGateStatus = "BLOCKED"
    elif not blockers:
        status = "READY_FOR_LOCAL_PILOT"
    else:
        status = "LOCAL_SYNTHETIC_ONLY_HOLD"
    body: dict[str, object] = {
        "schema_version": "release-gate-v1",
        "scope": "LOCAL_SYNTHETIC_ONLY",
        "checks": checks,
        "status": status,
        "blocking_requirements": sorted(blockers),
        "external_gates_pending": sorted(external_gates),
        "safety_violations": safety_violations,
        "wagering_enabled": inputs.wagering_enabled,
        "external_connectivity_enabled": inputs.external_connectivity_enabled,
        "activation_authority": "NONE",
        "promotion_authority": "NONE",
        "note": "Evidence aggregation only; human, rights, security and owner decisions remain required.",
    }
    body["report_hash"] = _hash_body(body)
    return body


def _hash_body(body: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def verify_release_gate_report(report: dict[str, object]) -> None:
    report_hash = report.get("report_hash")
    if not isinstance(report_hash, str) or report_hash != _hash_body({key: value for key, value in report.items() if key != "report_hash"}):
        raise ValueError("release gate report hash mismatch")
    if report.get("scope") != "LOCAL_SYNTHETIC_ONLY":
        raise ValueError("release gate scope must remain local synthetic only")
    if report.get("activation_authority") != "NONE" or report.get("promotion_authority") != "NONE":
        raise ValueError("release gate cannot grant activation or promotion authority")
    if report.get("wagering_enabled") or report.get("external_connectivity_enabled"):
        raise ValueError("release gate cannot pass with prohibited capabilities enabled")
    if report.get("status") == "READY_FOR_LOCAL_PILOT" and report.get("blocking_requirements"):
        raise ValueError("ready release gate cannot have blocking requirements")
