import json
from pathlib import Path

import pytest

from app.assurance_packet import build_s4_assurance_packet, verify_s4_assurance_packet


ROOT = Path(__file__).resolve().parents[3]


def test_s4_packet_is_fail_closed_and_machine_verifiable() -> None:
    packet = build_s4_assurance_packet(ROOT)

    verify_s4_assurance_packet(packet)
    assert packet["status"] == "LOCAL_SYNTHETIC_ONLY_HOLD"
    assert packet["activation_authority"] == "NONE"
    assert packet["promotion_authority"] == "NONE"
    assert any(gate["status"] == "BLOCKED_EXTERNAL_DEPENDENCY" for gate in packet["review_gates"])


def test_committed_s4_packet_is_verified_and_held() -> None:
    packet = json.loads((ROOT / "fixtures" / "synthetic" / "s4_assurance_packet_v1.json").read_text(encoding="utf-8"))

    verify_s4_assurance_packet(packet)
    assert packet["status"] == "LOCAL_SYNTHETIC_ONLY_HOLD"


def test_s4_packet_tampering_fails_closed() -> None:
    packet = build_s4_assurance_packet(ROOT)
    packet["status"] = "READY_FOR_PRODUCTION"

    with pytest.raises(ValueError, match="hash mismatch"):
        verify_s4_assurance_packet(packet)
