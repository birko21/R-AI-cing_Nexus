"""Prove the local synthetic ingestion-to-forecast path end to end."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.synthetic_acceptance import run_synthetic_vertical_proof  # noqa: E402


def main() -> None:
    print(json.dumps(run_synthetic_vertical_proof(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
