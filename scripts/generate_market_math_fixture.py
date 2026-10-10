from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.market import ingest_market_quote  # noqa: E402
from app.market_math import compare_market_quotes  # noqa: E402
from app.testsupport import NOW, quote_fixture  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "market_math_v1.json"


def quote(**overrides: object):
    raw = quote_fixture(overrides.pop("quote_id", "q"), overrides.pop("selection_id", "selection-1"), **overrides)
    result = ingest_market_quote(raw)
    assert result.quote is not None
    return result.quote


def build_fixture() -> dict[str, object]:
    comparable = compare_market_quotes([quote(quote_id="q1", selection_id="selection-1", price=2.0), quote(quote_id="q2", selection_id="selection-2", price=4.0)])
    scratched = compare_market_quotes([quote(quote_id="q1", selection_id="selection-1", runner_status="SCRATCHED"), quote(quote_id="q2", selection_id="selection-2")])
    timestamp_mismatch = compare_market_quotes([
        quote(quote_id="q1", selection_id="selection-1"),
        quote(quote_id="q2", selection_id="selection-2", source_timestamp=NOW + timedelta(minutes=6), retrieved_at=NOW + timedelta(minutes=6)),
    ])
    return {
        "schema_version": "market-math-v1",
        "comparable": comparable.to_dict(),
        "scratched_not_comparable": scratched.to_dict(),
        "timestamp_not_comparable": timestamp_mismatch.to_dict(),
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Reference math evidence only; no market recommendation or order operation is enabled.",
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
        raise SystemExit("MARKET MATH FIXTURE CHECK FAILED: generated content differs")
    print(f"MARKET MATH FIXTURE VALID: comparable={expected['comparable']['status']} scratched={expected['scratched_not_comparable']['status']}")


if __name__ == "__main__":
    main()
