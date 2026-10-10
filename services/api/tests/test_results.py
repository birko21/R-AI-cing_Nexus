from datetime import datetime, timezone

import pytest

from app.contracts import SelectionCreate
from app.results import OfficialResult, ResultReconciliationError, ResultRegistry
from app.selection_journal import SelectionJournal


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def selection(selection_type: str = "WIN", entry_id: str | None = "entry-1"):
    return SelectionJournal().create("owner", SelectionCreate(
        race_id="race-1", field_revision="field-r2", entry_id=entry_id, selection_type=selection_type,
        rationale="Deliberate fixture decision", forecast_id="forecast-1", quote_id="quote-1",
    ), NOW)


def result(**overrides: object) -> OfficialResult:
    values: dict[str, object] = {
        "result_id": "result-1", "race_id": "race-1", "field_revision": "field-r2", "source_receipt_id": "receipt-1",
        "status": "OFFICIAL", "observed_at": NOW, "official_at": NOW, "placings": {"entry-1": 1, "entry-2": 2},
        "data_mode": "SYNTHETIC_ONLY",
    }
    values.update(overrides)
    return OfficialResult(**values)


def test_reconciles_only_after_official_result_and_separates_paper_state() -> None:
    registry = ResultRegistry()
    pending = result(status="PENDING", official_at=None)
    with pytest.raises(ResultReconciliationError, match="official result"):
        registry.reconcile(selection(), pending, NOW)
    official = result()
    reconciliation = registry.reconcile(selection(), official, NOW)

    assert reconciliation.outcome == "WIN"
    snapshot = registry.snapshot()
    assert snapshot["paper_simulation_included"] is False
    assert snapshot["model_rankings_included"] is False


def test_preserves_correction_as_new_result_revision() -> None:
    registry = ResultRegistry()
    registry.append(result())
    correction = result(result_id="result-2", status="CORRECTED", correction_of="result-1", observed_at=datetime(2026, 1, 15, 1, tzinfo=timezone.utc), placings={"entry-1": 2, "entry-2": 1})
    registry.append(correction)

    assert registry.latest("race-1").result_id == "result-2"
    with pytest.raises(ResultReconciliationError, match="append-only"):
        registry.append(correction)


def test_dead_heat_scratch_void_pass_and_loss_outcomes_are_explicit() -> None:
    registry = ResultRegistry()
    assert registry.reconcile(selection(), result(result_id="result-1", dead_heat_groups=(("entry-1", "entry-2"),), scratched_entries=frozenset({"entry-3"}), placings={"entry-4": 4}), NOW).outcome == "DEAD_HEAT"
    assert registry.reconcile(selection(entry_id="entry-3"), result(result_id="result-2", dead_heat_groups=(("entry-1", "entry-2"),), scratched_entries=frozenset({"entry-3"}), placings={"entry-4": 4}), NOW).outcome == "SCRATCHED"
    assert registry.reconcile(selection(entry_id="entry-5"), result(result_id="result-3", dead_heat_groups=(("entry-1", "entry-2"),), scratched_entries=frozenset({"entry-3"}), placings={"entry-4": 4}), NOW).outcome == "VOID"
    assert registry.reconcile(selection(entry_id="entry-4"), result(result_id="result-4", dead_heat_groups=(("entry-1", "entry-2"),), scratched_entries=frozenset({"entry-3"}), placings={"entry-4": 4}), NOW).outcome == "LOSS"
    assert registry.reconcile(selection("PASS", None), result(result_id="result-5", dead_heat_groups=(("entry-1", "entry-2"),), scratched_entries=frozenset({"entry-3"}), placings={"entry-4": 4}), NOW).outcome == "PASS"


def test_correction_requires_existing_revision_and_reconciliation_is_append_only() -> None:
    registry = ResultRegistry()
    with pytest.raises(ResultReconciliationError, match="existing"):
        registry.append(result(status="CORRECTED", correction_of="missing"))
    official = result()
    registry.append(official)
    selected = selection()
    registry.reconcile(selected, official, NOW)
    with pytest.raises(ResultReconciliationError, match="append-only"):
        registry.reconcile(selected, official, NOW)
