from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.operations import BudgetConfig, OperationsLedger, UsageEvent  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "operations_v1.json"
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def build_fixture() -> dict[str, object]:
    ledger = OperationsLedger(BudgetConfig(daily_spend_aud=Decimal("1.00"), daily_tokens=10000))
    ledger.record(UsageEvent(job_id="job-1", provider="synthetic-provider", started_at=NOW, latency_ms=100, status="SUCCESS", input_tokens=100, output_tokens=100, estimated_spend_aud=Decimal("0.50")))
    ledger.record(UsageEvent(job_id="job-2", provider="synthetic-provider", started_at=NOW, latency_ms=200, status="ERROR", input_tokens=100, output_tokens=100, estimated_spend_aud=Decimal("0.50")))
    ledger.disable_provider("synthetic-provider")
    snapshot = ledger.snapshot()
    return {
        "schema_version": "operations-v1", "snapshot": snapshot,
        "outbound": {"noncritical_after_cap": ledger.outbound_allowed("other-provider", critical=False), "critical_after_cap": ledger.outbound_allowed("other-provider", critical=True), "disabled_provider": ledger.outbound_allowed("synthetic-provider", critical=True)},
        "fictional": True, "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Offline operations evidence only; provider is synthetic and no external work is enabled.",
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
        raise SystemExit("OPERATIONS FIXTURE CHECK FAILED: generated content differs")
    print(f"OPERATIONS FIXTURE VALID: jobs={expected['snapshot']['jobs']} alert={expected['snapshot']['alert_level']}")


if __name__ == "__main__":
    main()
