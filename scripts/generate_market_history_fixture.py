from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.market import ingest_market_quote  # noqa: E402
from app.market_history import MarketHistory  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "market_history_v1.json"
BASE = datetime(2026, 1, 15, 10, tzinfo=timezone.utc)


def quote(quote_id: str, source: datetime, retrieved: datetime, **overrides: object):
    raw: dict[str, object] = {
        "quote_id": quote_id,
        "mapping": {
            "mapping_id": "map-1", "code": "THOROUGHBRED", "race_id": "THOROUGHBRED:fixture:race-1",
            "field_revision": "field-r1", "entry_id": "THOROUGHBRED:fixture:entry-1", "market_source": "fixture",
            "market_id": "market-1", "selection_id": "selection-1",
        },
        "market_type": "WIN", "price_type": "DECIMAL", "price": 3.5,
        "source_timestamp": source, "retrieved_at": retrieved, "in_play": False,
        "entitlement_reference": "synthetic-fixture", "source_receipt_id": "receipt-1",
        "data_mode": "SYNTHETIC_ONLY", "rights_state": "SYNTHETIC",
    }
    raw.update(overrides)
    result = ingest_market_quote(raw)
    assert result.quote is not None
    return result.quote


def build_fixture() -> dict[str, object]:
    history = MarketHistory()
    history.append(quote("live", BASE, BASE + timedelta(minutes=1)))
    history.append(quote("closing", BASE + timedelta(hours=2), BASE + timedelta(hours=2), price_phase="CLOSING", price=2.0))
    return {
        "schema_version": "market-history-v1",
        "before_closing": history.as_of("map-1", BASE + timedelta(minutes=30)).to_dict(),
        "after_closing": history.as_of("map-1", BASE + timedelta(hours=3)).to_dict(),
        "missing_mapping": history.as_of("unknown-map", BASE + timedelta(hours=3)).to_dict(),
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Offline as-of replay evidence; closing prices are not substituted before their availability.",
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
        raise SystemExit("MARKET HISTORY FIXTURE CHECK FAILED: generated content differs")
    print(f"MARKET HISTORY FIXTURE VALID: before={expected['before_closing']['availability']} after={expected['after_closing']['availability']}")


if __name__ == "__main__":
    main()
