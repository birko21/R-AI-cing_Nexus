from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.evidence import validate_claim  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "evidence_claims_v1.json"
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def base_claim() -> dict[str, object]:
    return {
        "claim_id": "claim-1",
        "claim_type": "FACT",
        "text": "The synthetic fixture contains six races.",
        "source_ids": ["fixture:synthetic-v1"],
        "model_ids": ["B0_UNIFORM"],
        "observed_at": NOW,
        "limitations": ["Synthetic implementation evidence; not a live racing fact."],
        "data_mode": "SYNTHETIC_ONLY",
    }


def build_fixture() -> dict[str, object]:
    factual = validate_claim(base_claim()).model_dump(mode="json")
    probability = validate_claim({
        **base_claim(), "claim_id": "claim-2", "claim_type": "PROBABILITY",
        "text": "Illustrative probability for entry-1 is 0.42.", "numeric_value": 0.42,
        "probability_supported": True,
    }).model_dump(mode="json")
    rejected: list[dict[str, str]] = []
    for claim_type, values in (("PROBABILITY", {"numeric_value": 0.42}), ("CURRENTNESS", {}), ("SOURCE_ASSERTION", {})):
        try:
            validate_claim({**base_claim(), "claim_type": claim_type, **values})
        except ValueError as exc:
            rejected.append({"claim_type": claim_type, "reason": str(exc).splitlines()[0]})
    return {
        "schema_version": "evidence-claims-v1",
        "accepted": [factual, probability],
        "rejected": rejected,
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Evidence validator fixture only; no claim is licensed, official, current or validated real-world evidence.",
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
        raise SystemExit("EVIDENCE FIXTURE CHECK FAILED: generated content differs")
    print(f"EVIDENCE FIXTURE VALID: accepted={len(expected['accepted'])} rejected={len(expected['rejected'])}")


if __name__ == "__main__":
    main()
