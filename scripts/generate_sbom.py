from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "evidence" / "ril-057" / "sbom.json"


def build_sbom(root: Path = ROOT) -> dict[str, object]:
    requirements = []
    for line in (root / "services" / "api" / "requirements.lock.txt").read_text(encoding="utf-8").splitlines():
        if "==" in line and not line.startswith("#"):
            name, version = line.split("==", 1)
            requirements.append({"name": name, "version": version, "ecosystem": "PyPI"})
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    node = [{"name": name, "version": version, "ecosystem": "npm"} for section in ("dependencies", "devDependencies") for name, version in package.get(section, {}).items()]
    components = sorted(requirements + node, key=lambda item: (item["ecosystem"], item["name"].lower()))
    return {"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1, "components": components, "source_lockfiles": ["pnpm-lock.yaml", "services/api/requirements.lock.txt"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_sbom()
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("SBOM CHECK FAILED: generated content differs")
    print(f"SBOM VALID: components={len(expected['components'])}")


if __name__ == "__main__":
    main()
