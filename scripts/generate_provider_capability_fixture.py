from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.providers import PaginationCapability, ProviderCapabilities, QuotaCapability  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "provider_capabilities_v1.json"


def build_fixture() -> dict[str, object]:
    provider = ProviderCapabilities(
        provider_id="synthetic-fixture",
        display_name="Synthetic fixture adapter",
        supported_codes=frozenset({"THOROUGHBRED", "HARNESS", "GREYHOUND"}),
        supported_fields=frozenset({"meeting", "race", "entry", "result"}),
        timestamp_fields=frozenset({"retrieved_at", "first_observed_at", "published_at"}),
        data_mode="SYNTHETIC_ONLY",
        rights_state="SYNTHETIC",
        pagination=PaginationCapability(True, "CURSOR", 100),
        quotas=QuotaCapability(requests_per_minute=60, daily_requests=1000, concurrent_requests=2),
        supported_operations=frozenset({"LIST_MEETINGS", "GET_RACES", "GET_ENTRIES", "GET_RESULTS"}),
        unsupported_operations=frozenset({"GET_MARKETS"}),
    )
    return {
        "schema_version": "provider-capability-v1",
        "providers": [provider.to_dict()],
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Capability matrix evidence only; no external provider is enabled.",
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
        raise SystemExit("PROVIDER CAPABILITY FIXTURE CHECK FAILED: generated content differs")
    print(f"PROVIDER CAPABILITY FIXTURE VALID: providers={len(expected['providers'])}")


if __name__ == "__main__":
    main()
