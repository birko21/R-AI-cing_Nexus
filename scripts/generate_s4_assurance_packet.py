"""Generate and verify the fail-closed S4 assurance packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.assurance_packet import build_s4_assurance_packet, verify_s4_assurance_packet  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "s4_assurance_packet_v1.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_s4_assurance_packet(ROOT)
    verify_s4_assurance_packet(expected)
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("S4 ASSURANCE PACKET CHECK FAILED: generated content differs")
    print(f"S4 ASSURANCE PACKET VALID: status={expected['status']} hash={expected['packet_hash']}")


if __name__ == "__main__":
    main()
