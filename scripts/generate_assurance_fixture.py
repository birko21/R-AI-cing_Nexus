"""Generate and validate the pending synthetic model-assurance packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.assurance import build_assurance_packet, verify_assurance_packet  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "assurance_packet_v1.json"


def build_fixture() -> dict[str, object]:
    packet = build_assurance_packet(
        artifact_id="B1_FORM_HEURISTIC:synthetic-v1",
        evaluation_id="synthetic-evaluation-v1",
        split_manifest_hash="synthetic-split-manifest-v1",
    )
    verify_assurance_packet(packet)
    return packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("ASSURANCE FIXTURE CHECK FAILED: generated content differs")
    print(f"ASSURANCE FIXTURE VALID: status={expected['status']} hash={expected['packet_hash']}")


if __name__ == "__main__":
    main()
