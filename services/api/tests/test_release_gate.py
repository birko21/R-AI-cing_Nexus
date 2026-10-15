import json
from pathlib import Path

import pytest

from app.release_gate import ReleaseGateInputs, build_release_gate_report, verify_release_gate_report


ROOT = Path(__file__).resolve().parents[3]


def test_release_gate_is_explicitly_held_without_owner_and_review_decisions() -> None:
    report = build_release_gate_report(ReleaseGateInputs(local_evidence_complete=True, automated_checks_passed=True))

    verify_release_gate_report(report)
    assert report["status"] == "LOCAL_SYNTHETIC_ONLY_HOLD"
    assert report["activation_authority"] == "NONE"
    assert "owner_approval" in report["blocking_requirements"]
    assert report["external_gates_pending"] == ["approved_oidc", "real_source_rights"]


def test_local_pilot_requires_review_but_not_live_provider_approval() -> None:
    report = build_release_gate_report(
        ReleaseGateInputs(
            local_evidence_complete=True,
            automated_checks_passed=True,
            owner_approval=True,
            visual_review_complete=True,
            accessibility_review_complete=True,
            model_assurance_complete=True,
        )
    )

    verify_release_gate_report(report)
    assert report["status"] == "READY_FOR_LOCAL_PILOT"
    assert report["blocking_requirements"] == []
    assert report["external_gates_pending"] == ["approved_oidc", "real_source_rights"]


def test_prohibited_capabilities_block_and_tampering_fails_closed() -> None:
    report = build_release_gate_report(
        ReleaseGateInputs(local_evidence_complete=True, automated_checks_passed=True, external_connectivity_enabled=True)
    )
    assert report["status"] == "BLOCKED"
    with pytest.raises(ValueError, match="prohibited capabilities"):
        verify_release_gate_report(report)

    pending = build_release_gate_report(ReleaseGateInputs(local_evidence_complete=True, automated_checks_passed=True))
    tampered = dict(pending)
    tampered["status"] = "READY_FOR_LOCAL_PILOT"
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_release_gate_report(tampered)


def test_committed_release_gate_fixture_is_verified_and_pending() -> None:
    report = json.loads((ROOT / "fixtures" / "synthetic" / "release_gate_v1.json").read_text(encoding="utf-8"))
    verify_release_gate_report(report)
    assert report["status"] == "LOCAL_SYNTHETIC_ONLY_HOLD"
