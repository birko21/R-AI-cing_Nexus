"""Validate the locally completable release boundary without activating it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "evidence" / "ril-060" / "safe-completion-gate.json"
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.assurance_packet import build_s4_assurance_packet, verify_s4_assurance_packet  # noqa: E402
from app.release_gate import verify_release_gate_report  # noqa: E402


def _hash_body(body: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _command(name: str, args: list[str]) -> dict[str, object]:
    result = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
    return {"name": name, "command": args, "exit_code": result.returncode, "output_tail": result.stdout[-500:]}


def build_gate() -> dict[str, object]:
    packet = build_s4_assurance_packet(ROOT)
    verify_s4_assurance_packet(packet)
    release_gate = packet["release_gate"]
    assert isinstance(release_gate, dict)
    verify_release_gate_report(release_gate)
    checks = [
        _command("render_blueprint", ["scripts/validate_render_blueprint.py"]),
        _command("security_audit", ["scripts/security_audit.py"]),
        _command("s4_packet", ["scripts/generate_s4_assurance_packet.py"]),
    ]
    if any(check["exit_code"] != 0 for check in checks):
        status = "BLOCKED"
    elif packet["status"] != "LOCAL_SYNTHETIC_ONLY_HOLD":
        status = "BLOCKED"
    else:
        status = "LOCAL_SYNTHETIC_ONLY_HOLD"
    body: dict[str, object] = {
        "schema_version": "safe-completion-gate-v1",
        "status": status,
        "scope": "LOCAL_SYNTHETIC_ONLY",
        "machine_checks": checks,
        "assurance_packet_hash": packet["packet_hash"],
        "release_gate_hash": release_gate["report_hash"],
        "external_gates_pending": release_gate["external_gates_pending"],
        "human_gates_pending": release_gate["blocking_requirements"],
        "external_connectivity_enabled": False,
        "wagering_enabled": False,
        "activation_authority": "NONE",
        "promotion_authority": "NONE",
        "note": "Local completion evidence is valid; external and human gates remain explicit and unapproved.",
    }
    body["gate_hash"] = _hash_body(body)
    return body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    report = build_gate()
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.is_file() or json.loads(args.output.read_text(encoding="utf-8")) != report:
        raise SystemExit("SAFE COMPLETION GATE CHECK FAILED: generated content differs")
    print(f"SAFE COMPLETION GATE VALID: status={report['status']} hash={report['gate_hash']}")


if __name__ == "__main__":
    main()
