from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.paper import PaperAssumptions, PaperLedger  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "paper_settlement_v1.json"


def build_fixture() -> dict[str, object]:
    ledger = PaperLedger(PaperAssumptions(fee_rate=0.02, commission_rate=0.1, fill_ratio=0.5, max_exposure=100))
    ledger.record_position("p-win", "selection-1", 10, 3, 20)
    ledger.settle("p-win", "WIN")
    ledger.record_position("p-dead-heat", "selection-2", 10, 5, 4)
    ledger.settle("p-dead-heat", "DEAD_HEAT", removal_factor=0.2, dead_heat_places=2)
    ledger.record_position("p-scratch", "selection-3", 10, 4, 20, scratched=True)
    ledger.settle("p-scratch", "SCRATCHED")
    ledger.record_position("p-void", "selection-4", 10, 4, 20)
    ledger.settle("p-void", "VOID")
    return {
        "schema_version": "paper-settlement-v1",
        "ledger": ledger.snapshot(),
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_PAPER_ONLY_DO_NOT_TREAT_AS_LIVE",
        "note": "Scenario ledger evidence only; no external execution, guaranteed return or live wagering path exists.",
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
        raise SystemExit("PAPER SETTLEMENT FIXTURE CHECK FAILED: generated content differs")
    print(f"PAPER SETTLEMENT FIXTURE VALID: positions={len(expected['ledger']['positions'])} settlements={len(expected['ledger']['settlements'])}")


if __name__ == "__main__":
    main()
