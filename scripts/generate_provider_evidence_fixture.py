"""Validate the synthetic provider-evidence registry fixture."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.provider_evidence import ProviderEvidenceRecord, ProviderEvidenceRegistry  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "provider_evidence_v1.json"


def build_fixture() -> dict[str, object]:
    registry = ProviderEvidenceRegistry()
    registry.register(
        ProviderEvidenceRecord(
            evidence_id="synthetic-fixture-contract-v1",
            provider_id="synthetic-fixture",
            capability="races, entries, results and bounded pagination",
            source_reference="docs/models/PROVIDER_ADAPTER_CONTRACT.md",
            observed_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            evidence_status="OBSERVED",
            data_mode="SYNTHETIC_ONLY",
            rights_state="SYNTHETIC",
            notes="Offline contract evidence only; no external provider is enabled.",
        )
    )
    return {
        **registry.snapshot(),
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
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
        raise SystemExit("PROVIDER EVIDENCE FIXTURE CHECK FAILED: generated content differs")
    print(f"PROVIDER EVIDENCE FIXTURE VALID: records={len(expected['records'])} activation={expected['activation_authority']}")


if __name__ == "__main__":
    main()
