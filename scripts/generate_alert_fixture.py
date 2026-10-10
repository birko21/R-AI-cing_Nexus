from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.alerts import AlertRouter, ChangeEvent  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "alerts_v1.json"
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def event(event_id: str, cause: str, *, observed_at: datetime = NOW, expires_at: datetime = NOW + timedelta(hours=1)) -> ChangeEvent:
    return ChangeEvent(event_id, "watch-1", "source-a", "receipt-1", observed_at, "CONFIRMED", True, "watch-1:field-change", cause, expires_at)


def build_fixture() -> dict[str, object]:
    router = AlertRouter()
    first = router.ingest(event("event-1", "confirmed field revision"), NOW)
    duplicate = router.ingest(event("event-2", "replayed field revision"), NOW + timedelta(minutes=1))
    expired = router.ingest(event("event-3", "new field revision", observed_at=NOW + timedelta(hours=2), expires_at=NOW + timedelta(hours=3)), NOW + timedelta(hours=2))
    assert first is not None and duplicate == first and expired is not None
    return {
        "schema_version": "alerts-v1",
        "first": first.to_dict(), "duplicate_replay": duplicate.to_dict(), "after_expiry": expired.to_dict(),
        "fictional": True, "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Alert dedupe evidence only; no external notification or wagering path is enabled.",
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
        raise SystemExit("ALERT FIXTURE CHECK FAILED: generated content differs")
    print(f"ALERT FIXTURE VALID: first={expected['first']['status']} deduped={expected['duplicate_replay']['alert_id'] == expected['first']['alert_id']}")


if __name__ == "__main__":
    main()
