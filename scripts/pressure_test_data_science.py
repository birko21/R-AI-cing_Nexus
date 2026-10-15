"""Repeat deterministic synthetic data-science evidence and compare hashes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "evidence" / "ril-061" / "data-science-pressure.json"
ARTIFACTS = (
    ROOT / "docs" / "evidence" / "ril-061" / "research-output.json",
    ROOT / "docs" / "evidence" / "ril-061" / "model-evaluation.json",
    ROOT / "docs" / "evidence" / "ril-061" / "provider-readiness.json",
    ROOT / "docs" / "evidence" / "ril-061" / "b3-synthetic-evaluation.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(script: str) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)


def _validate_b3() -> dict[str, object]:
    payload = json.loads(ARTIFACTS[-1].read_text(encoding="utf-8"))
    models = payload.get("models")
    if not isinstance(models, list) or len(models) != 6:
        raise AssertionError("B3 evidence must contain six code/backend records")
    codes = sorted({item.get("code") for item in models if isinstance(item, dict)})
    backends = sorted({item.get("backend") for item in models if isinstance(item, dict)})
    if codes != ["GREYHOUND", "HARNESS", "THOROUGHBRED"] or backends != ["catboost", "lightgbm"]:
        raise AssertionError("B3 evidence must cover all three codes and both backends")
    if payload.get("status") != "ILLUSTRATIVE_SYNTHETIC_ONLY" or payload.get("validated_claim") is not False:
        raise AssertionError("B3 evidence must remain synthetic and non-predictive")
    return {"codes": codes, "backends": backends, "models": len(models)}


def main() -> None:
    repetitions: list[dict[str, str]] = []
    for _ in range(2):
        _run("generate_ril061_evidence.py")
        _run("generate_b3_synthetic_evidence.py")
        repetitions.append({str(path.relative_to(ROOT)): _sha256(path) for path in ARTIFACTS if path.is_file()})
    missing = [str(path) for path in ARTIFACTS if not path.is_file()]
    if missing:
        raise SystemExit(f"DATA-SCIENCE PRESSURE FAIL: missing artifacts {missing}")
    if len(repetitions) != 2 or repetitions[0] != repetitions[1]:
        raise SystemExit(f"DATA-SCIENCE PRESSURE FAIL: repeated artifact hashes differ: {repetitions}")
    hashes = repetitions[-1]
    metadata = _validate_b3()
    report = {
        "schema_version": "data-science-pressure-v1",
        "status": "PASS",
        "repetitions": 2,
        "artifacts": hashes,
        "coverage": metadata,
        "data_mode": "SYNTHETIC_ONLY",
        "validated_claim": False,
        "promotion_authority": "NONE",
        "note": "Repeated deterministic benchmark and B3 generation produced identical artifact hashes; no real-world performance claim is made.",
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
