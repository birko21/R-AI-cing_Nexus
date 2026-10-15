"""Manual model-assurance packet and fail-closed promotion readiness gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Literal


CheckStatus = Literal["PENDING", "PASS", "FAIL"]
AssuranceStatus = Literal["HOLD", "PASS", "FAIL"]


@dataclass(frozen=True)
class AssurancePacket:
    schema_version: str
    artifact_id: str
    evaluation_id: str
    split_manifest_hash: str
    leakage_audit: CheckStatus
    split_review: CheckStatus
    calibration_review: CheckStatus
    reviewer_reference: str | None
    owner_decision_reference: str | None
    owner_approval: bool
    status: AssuranceStatus
    missing_requirements: tuple[str, ...]
    promotion_authority: Literal["NONE"]
    packet_hash: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["missing_requirements"] = list(self.missing_requirements)
        return payload


def build_assurance_packet(
    *,
    artifact_id: str,
    evaluation_id: str,
    split_manifest_hash: str,
    leakage_audit: CheckStatus = "PENDING",
    split_review: CheckStatus = "PENDING",
    calibration_review: CheckStatus = "PENDING",
    reviewer_reference: str | None = None,
    owner_decision_reference: str | None = None,
    owner_approval: bool = False,
) -> dict[str, object]:
    """Build a packet; only explicit manual references can move it beyond HOLD."""

    if not artifact_id.strip() or not evaluation_id.strip() or not split_manifest_hash.strip():
        raise ValueError("assurance identity fields are required")
    checks = {"leakage_audit": leakage_audit, "split_review": split_review, "calibration_review": calibration_review}
    if any(value not in {"PENDING", "PASS", "FAIL"} for value in checks.values()):
        raise ValueError("assurance check status is unsupported")
    missing = [name for name, value in checks.items() if value != "PASS"]
    if not reviewer_reference:
        missing.append("independent_reviewer_reference")
    if not owner_decision_reference or not owner_approval:
        missing.append("owner_approval_reference")
    status: AssuranceStatus = "FAIL" if any(value == "FAIL" for value in checks.values()) else "PASS" if not missing else "HOLD"
    body: dict[str, object] = {
        "schema_version": "model-assurance-packet-v1",
        "artifact_id": artifact_id,
        "evaluation_id": evaluation_id,
        "split_manifest_hash": split_manifest_hash,
        **checks,
        "reviewer_reference": reviewer_reference,
        "owner_decision_reference": owner_decision_reference,
        "owner_approval": owner_approval,
        "status": status,
        "missing_requirements": sorted(set(missing)),
        "promotion_authority": "NONE",
    }
    body["packet_hash"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
    return body


def verify_assurance_packet(packet: dict[str, object]) -> None:
    packet_hash = packet.get("packet_hash")
    if not isinstance(packet_hash, str):
        raise ValueError("assurance packet hash is required")
    body = {key: value for key, value in packet.items() if key != "packet_hash"}
    expected = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
    if packet_hash != expected:
        raise ValueError("assurance packet hash mismatch")
    if packet.get("promotion_authority") != "NONE":
        raise ValueError("assurance packet cannot grant promotion authority")
    if packet.get("status") == "PASS" and packet.get("missing_requirements"):
        raise ValueError("passing assurance packet cannot have missing requirements")
