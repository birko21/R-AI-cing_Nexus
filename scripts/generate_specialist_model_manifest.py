"""Validate deterministic synthetic manifests for the three specialist lanes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.specialist_models import specialist_model_manifest  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "specialist_models_v1.json"
CODES = ("GREYHOUND", "HARNESS", "THOROUGHBRED")
FAMILIES = ("COMBINED", "FORM_ONLY", "MARKET_ONLY")


def build_fixture() -> dict[str, object]:
    models = [
        specialist_model_manifest(code, family)
        for code in CODES
        for family in FAMILIES
    ]
    body: dict[str, object] = {
        "schema_version": "specialist-model-manifests-v1",
        "fictional": True,
        "data_mode": "SYNTHETIC_ONLY",
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "model_status": "ILLUSTRATIVE_NOT_VALIDATED",
        "models": models,
        "note": "Independent code/family contracts only; no model was fitted or promoted.",
    }
    body["manifest_hash"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("SPECIALIST MODEL MANIFEST CHECK FAILED: generated content differs")
    print(f"SPECIALIST MODEL MANIFEST VALID: models={len(expected['models'])} hash={expected['manifest_hash']}")


if __name__ == "__main__":
    main()
