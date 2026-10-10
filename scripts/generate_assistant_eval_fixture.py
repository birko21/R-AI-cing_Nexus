from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.assistant_eval import AssistantPolicy, BudgetConfig, BudgetLedger, DEFAULT_CASES, evaluate_cases, reference_responder  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "assistant_eval_v1.json"


def build_fixture() -> dict[str, object]:
    report = evaluate_cases(DEFAULT_CASES, reference_responder)
    ledger = BudgetLedger(BudgetConfig(max_requests=1, max_input_tokens=10, max_output_tokens=10, max_spend_usd=Decimal("0.10")))
    first = ledger.reserve(input_tokens=5, output_tokens=5, spend_usd=Decimal("0.05"))
    killed = ledger.reserve(input_tokens=1, output_tokens=1, spend_usd=Decimal("0.01"))
    return {
        "schema_version": "assistant-eval-v1",
        "report": report.model_dump(mode="json"),
        "budget_kill": {"first": first, "second": killed, "requests_recorded": ledger.requests, "spend_usd": str(ledger.spend_usd)},
        "policy_default": AssistantPolicy().status(),
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Offline evaluation and budget evidence only; assistant feature remains disabled pending rights and provider policy approval.",
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
        raise SystemExit("ASSISTANT EVAL FIXTURE CHECK FAILED: generated content differs")
    print(f"ASSISTANT EVAL FIXTURE VALID: passed={expected['report']['passed']} budget_second={expected['budget_kill']['second']} policy={expected['policy_default']}")


if __name__ == "__main__":
    main()
