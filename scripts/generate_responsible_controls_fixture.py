from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.contracts import SelectionCreate  # noqa: E402
from app.responsible import SessionControls, export_annotations, summarize_journal  # noqa: E402
from app.selection_journal import SelectionJournal  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "responsible_controls_v1.json"
NOW = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)


def build_fixture() -> dict[str, object]:
    journal = SelectionJournal()
    selection = journal.create("owner", SelectionCreate(race_id="race-1", field_revision="field-r1", entry_id=None, selection_type="PASS", rationale="Insufficient evidence"), NOW)
    selections = [selection]
    summary = summarize_journal(selections)
    exported = export_annotations(selections, [], permitted=True)
    controls = SessionControls()
    return {
        "schema_version": "responsible-controls-v1",
        "summary": summary.to_dict(), "annotation_export": exported,
        "session_decision": {"status": controls.decide(NOW, NOW)[0], "reason": controls.decide(NOW, NOW)[1]},
        "fictional": True, "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Responsible-use control evidence only; raw prices and forecast payloads are excluded.",
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
        raise SystemExit("RESPONSIBLE CONTROLS FIXTURE CHECK FAILED: generated content differs")
    print(f"RESPONSIBLE CONTROLS FIXTURE VALID: selection_count={expected['summary']['selection_count']} export={expected['annotation_export']['export_type']}")


if __name__ == "__main__":
    main()
