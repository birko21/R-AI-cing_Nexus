from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.watchlists import WatchlistRegistry  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "watchlist_v1.json"
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def build_fixture() -> dict[str, object]:
    registry = WatchlistRegistry()
    target = registry.create("THOROUGHBRED:stable:runner-1", "RUNNER", "THOROUGHBRED", "source-a", "runner-1", "Old Name", NOW)
    registry.identity_change(target.watch_id, source_system="source-b", source_id="runner-1-new", name="Updated Name", now=NOW, detail="provider migration")
    registry.pause(target.watch_id, NOW)
    return {
        "schema_version": "watchlist-v1",
        "current": registry.current(target.watch_id).__dict__,
        "history": [event.__dict__ for event in registry.history(target.watch_id)],
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Identity continuity evidence only; no alert or external execution path is enabled.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != json.loads(json.dumps(expected, default=str)):
        raise SystemExit("WATCHLIST FIXTURE CHECK FAILED: generated content differs")
    print(f"WATCHLIST FIXTURE VALID: state={expected['current']['state']} events={len(expected['history'])}")


if __name__ == "__main__":
    main()
