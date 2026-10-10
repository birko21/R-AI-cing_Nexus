"""Validate the checked-in API contract without contacting any service."""

from __future__ import annotations

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    document = yaml.safe_load((ROOT / "contracts" / "openapi_mvp.yaml").read_text(encoding="utf-8"))
    if document.get("openapi") != "3.1.0" or not document.get("paths") or not document.get("components", {}).get("schemas"):
        raise SystemExit("OpenAPI contract is incomplete")
    if "bearerAuth" not in document["components"].get("securitySchemes", {}):
        raise SystemExit("OpenAPI contract is missing bearerAuth")
    typescript = (ROOT / "contracts" / "types.ts").read_text(encoding="utf-8")
    if "export" not in typescript or "Forecast" not in typescript:
        raise SystemExit("TypeScript contract types are incomplete")
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (ROOT / "services" / "api" / "app", ROOT / "apps" / "web" / "src")
        for path in root.rglob("*.py" if root.name == "app" else "*.tsx")
    )
    if re.search(r"(?i)place_order|submit_order|auto.?stake|/order(?:\b|/)", source_text):
        raise SystemExit("contract validation found a wagering or trading operation")
    print(f"CONTRACT VALID: openapi_paths={len(document['paths'])} schemas={len(document['components']['schemas'])}")


if __name__ == "__main__":
    main()
