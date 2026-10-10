from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.contracts import SelectionCreate  # noqa: E402
from app.results import OfficialResult, ResultRegistry  # noqa: E402
from app.selection_journal import SelectionJournal  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "result_reconciliation_v1.json"
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def build_fixture() -> dict[str, object]:
    journal = SelectionJournal()
    selection = journal.create("local-owner", SelectionCreate(
        race_id="race-1", field_revision="field-r2", entry_id="entry-1", selection_type="WIN",
        rationale="Fixture decision", forecast_id="forecast-1", quote_id="quote-1",
    ), NOW)
    registry = ResultRegistry()
    original = OfficialResult(
        result_id="result-1", race_id="race-1", field_revision="field-r2", source_receipt_id="receipt-1",
        status="OFFICIAL", observed_at=NOW, official_at=NOW, placings={"entry-1": 1, "entry-2": 2}, data_mode="SYNTHETIC_ONLY",
    )
    corrected = original.model_copy(update={
        "result_id": "result-2", "status": "CORRECTED", "correction_of": "result-1",
        "observed_at": datetime(2026, 1, 15, 1, tzinfo=timezone.utc), "placings": {"entry-1": 2, "entry-2": 1},
    })
    registry.append(original)
    registry.append(corrected)
    first = registry.reconcile(selection, original, NOW)
    corrected_outcome = registry.reconcile(selection, corrected, datetime(2026, 1, 15, 1, tzinfo=timezone.utc))
    return {
        "schema_version": "result-reconciliation-v1",
        "original_outcome": first.__dict__,
        "corrected_outcome": corrected_outcome.__dict__,
        "latest_result_id": registry.latest("race-1").result_id if registry.latest("race-1") else None,
        "registry": registry.snapshot(),
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Official-result revision evidence only; paper simulation and model rankings are separate.",
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
        raise SystemExit("RESULT RECONCILIATION FIXTURE CHECK FAILED: generated content differs")
    print(f"RESULT RECONCILIATION FIXTURE VALID: original={expected['original_outcome']['outcome']} corrected={expected['corrected_outcome']['outcome']}")


if __name__ == "__main__":
    main()
