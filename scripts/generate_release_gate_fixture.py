"""Generate and validate the pending synthetic release-gate report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.release_gate import ReleaseGateInputs, build_release_gate_report, verify_release_gate_report  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "release_gate_v1.json"


def build_fixture() -> dict[str, object]:
    report = build_release_gate_report(ReleaseGateInputs(local_evidence_complete=True, automated_checks_passed=True))
    verify_release_gate_report(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("RELEASE GATE FIXTURE CHECK FAILED: generated content differs")
    print(f"RELEASE GATE FIXTURE VALID: status={expected['status']} hash={expected['report_hash']}")


if __name__ == "__main__":
    main()
