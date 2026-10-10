from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.research_tools import ResearchToolRegistry, ResearchToolRequest  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "research_tools_v1.json"
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def build_fixture() -> dict[str, object]:
    registry = ResearchToolRegistry()
    registry.register("races", lambda as_of, limit, args: [{"race_id": "race-1", "as_of": as_of.isoformat()}])
    request = ResearchToolRequest(tool="races", user_id="owner", as_of=NOW, limit=25)
    allowed = registry.execute(request, scopes={"races:read"}).model_dump(mode="json")
    denied = registry.execute(ResearchToolRequest(tool="markets", user_id="owner", as_of=NOW), scopes={"races:read"}).model_dump(mode="json")
    return {
        "schema_version": "research-tools-v1", "catalog": registry.catalog(), "allowed": allowed, "denied": denied,
        "fictional": True, "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Read-only tool contract evidence; no external tool or live source is enabled.",
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
        raise SystemExit("RESEARCH TOOL FIXTURE CHECK FAILED: generated content differs")
    print(f"RESEARCH TOOL FIXTURE VALID: tools={len(expected['catalog'])} allowed={expected['allowed']['status']} denied={expected['denied']['status']}")


if __name__ == "__main__":
    main()
