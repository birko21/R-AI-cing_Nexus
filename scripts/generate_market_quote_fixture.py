from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.market import ingest_market_quote  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "market_quotes_v1.json"
NOW = datetime(2026, 1, 15, 10, tzinfo=timezone.utc)


def raw_quote(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "quote_id": "quote-1",
        "mapping": {
            "mapping_id": "map-1", "code": "THOROUGHBRED", "race_id": "THOROUGHBRED:fixture:race-1",
            "field_revision": "field-r1", "entry_id": "THOROUGHBRED:fixture:entry-1", "market_source": "fixture",
            "market_id": "market-1", "selection_id": "selection-1",
        },
        "market_type": "WIN", "price_type": "DECIMAL", "price": 3.5,
        "source_timestamp": NOW, "retrieved_at": NOW, "in_play": False,
        "size": 100.0, "liquidity": 1000.0, "entitlement_reference": "synthetic-fixture",
        "source_receipt_id": "receipt-1", "data_mode": "SYNTHETIC_ONLY", "rights_state": "SYNTHETIC",
    }
    value.update(overrides)
    return value


def build_fixture() -> dict[str, object]:
    accepted = ingest_market_quote(raw_quote())
    quarantined = ingest_market_quote(raw_quote(mapping={"runner_name": "name-only"}))
    assert accepted.quote is not None and quarantined.quarantine is not None
    return {
        "schema_version": "market-quotes-v1",
        "accepted_quote": accepted.quote.model_dump(mode="json"),
        "mapping_quarantine": quarantined.quarantine.model_dump(mode="json"),
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Paper-analysis contract evidence only; no live odds or order path is enabled.",
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
        raise SystemExit("MARKET QUOTE FIXTURE CHECK FAILED: generated content differs")
    print(f"MARKET QUOTE FIXTURE VALID: mapping={expected['accepted_quote']['mapping']['entry_id']} quarantine={expected['mapping_quarantine']['reason_code']}")


if __name__ == "__main__":
    main()
