from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "fixtures" / "synthetic" / "scraping_policy_v1.json"


def build_fixture() -> dict[str, object]:
    return {
        "schema_version": "scraping-policy-v1",
        "data_mode": "SCRAPED_PUBLIC",
        "allowed_url_prefixes": ["https://public.example/racing/"],
        "user_agent": "RacingIntelligenceLab/0.1 (+research@example.invalid)",
        "timeout_seconds": 10.0,
        "minimum_interval_seconds": 1.0,
        "max_retries": 2,
        "robots_required": True,
        "terms_permission_required": True,
        "kill_switch_default": False,
        "blocked_access_statuses": [401, 402, 403, 407, 408, 409, 451],
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Policy fixture only; no real source is enabled.",
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
        raise SystemExit("SCRAPING POLICY FIXTURE CHECK FAILED: generated content differs")
    print(f"SCRAPING POLICY FIXTURE VALID: prefixes={len(expected['allowed_url_prefixes'])} mode={expected['data_mode']}")


if __name__ == "__main__":
    main()
