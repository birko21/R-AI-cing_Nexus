from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.source_approval import SourceApprovalRecord, UnavailableSourceStub, evaluate_source_approval  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "source_checkpoint_v1.json"


def build_fixture() -> dict[str, object]:
    checkpoint = evaluate_source_approval(SourceApprovalRecord("first-real-source-pending"))
    return {
        "schema_version": "source-checkpoint-v1",
        "checkpoint": checkpoint.to_dict(),
        "unavailable_response": UnavailableSourceStub(checkpoint).request("LIST_MEETINGS"),
        "fictional": True,
        "watermark": "BLOCKED_EXTERNAL_DEPENDENCY_DO_NOT_TREAT_AS_APPROVED",
        "note": "No provider rights, credentials, or external source are recorded.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("SOURCE CHECKPOINT FIXTURE CHECK FAILED: generated content differs")
    print(f"SOURCE CHECKPOINT FIXTURE VALID: status={expected['checkpoint']['status']}")


if __name__ == "__main__":
    main()
