import json
from pathlib import Path

import pytest

from app.assurance import build_assurance_packet, verify_assurance_packet


ROOT = Path(__file__).resolve().parents[3]


def test_assurance_packet_defaults_to_hold_without_human_decisions() -> None:
    packet = build_assurance_packet(artifact_id="artifact-1", evaluation_id="eval-1", split_manifest_hash="split-1")

    verify_assurance_packet(packet)
    assert packet["status"] == "HOLD"
    assert packet["promotion_authority"] == "NONE"
    assert set(packet["missing_requirements"]) == {
        "leakage_audit", "split_review", "calibration_review", "independent_reviewer_reference", "owner_approval_reference",
    }


def test_assurance_pass_requires_every_check_and_both_manual_references() -> None:
    held = build_assurance_packet(
        artifact_id="artifact-1", evaluation_id="eval-1", split_manifest_hash="split-1",
        leakage_audit="PASS", split_review="PASS", calibration_review="PASS", reviewer_reference="review-1",
    )
    assert held["status"] == "HOLD"
    passed = build_assurance_packet(
        artifact_id="artifact-1", evaluation_id="eval-1", split_manifest_hash="split-1",
        leakage_audit="PASS", split_review="PASS", calibration_review="PASS", reviewer_reference="review-1",
        owner_decision_reference="owner-decision-1", owner_approval=True,
    )
    verify_assurance_packet(passed)
    assert passed["status"] == "PASS"
    assert passed["missing_requirements"] == []


def test_failed_assurance_and_tampered_packet_fail_closed() -> None:
    failed = build_assurance_packet(
        artifact_id="artifact-1", evaluation_id="eval-1", split_manifest_hash="split-1", leakage_audit="FAIL",
    )
    assert failed["status"] == "FAIL"
    tampered = dict(failed)
    tampered["promotion_authority"] = "CHAMPION"
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_assurance_packet(tampered)


def test_committed_assurance_fixture_is_pending_and_hash_verified() -> None:
    packet = json.loads((ROOT / "fixtures" / "synthetic" / "assurance_packet_v1.json").read_text(encoding="utf-8"))
    verify_assurance_packet(packet)
    assert packet["status"] == "HOLD"
    assert packet["owner_approval"] is False
