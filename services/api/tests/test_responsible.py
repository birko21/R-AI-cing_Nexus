from datetime import datetime, time, timedelta, timezone

import pytest

from app.contracts import SelectionAddendumCreate, SelectionCreate
from app.responsible import AnnotationExportError, SessionControls, summarize_journal, export_annotations, validate_responsible_copy
from app.selection_journal import SelectionJournal


NOW = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)


def journal_items():
    journal = SelectionJournal()
    first = journal.create("owner", SelectionCreate(race_id="race-1", field_revision="field-r1", entry_id="entry-1", selection_type="WIN", rationale="Evidence-based note", forecast_id="forecast-1"), NOW)
    passed = journal.create("owner", SelectionCreate(race_id="race-2", field_revision="field-r1", entry_id=None, selection_type="PASS", rationale="Insufficient evidence"), NOW)
    addendum = journal.addendum("owner", first.selection_id, SelectionAddendumCreate(note="Reflection addendum"), NOW)
    return [first, passed], [addendum]


def test_summary_keeps_selections_and_forecast_references_separate() -> None:
    selections, _ = journal_items()
    summary = summarize_journal(selections)
    assert summary.selection_count == 2
    assert summary.win_count == 1 and summary.pass_count == 1
    assert summary.forecast_reference_count == 1
    assert summary.paper_simulation_included is False


def test_annotation_export_is_permitted_and_excludes_raw_payloads() -> None:
    selections, addenda = journal_items()
    export = export_annotations(selections, addenda, permitted=True)
    assert export["export_type"] == "ANNOTATIONS_ONLY"
    assert export["raw_prices_included"] is False
    assert export["forecast_payloads_included"] is False
    with pytest.raises(AnnotationExportError, match="not permitted"):
        export_annotations(selections, addenda, permitted=False)


def test_pause_quiet_hours_and_session_limit_are_explicit() -> None:
    controls = SessionControls(quiet_hours_start=time(22), quiet_hours_end=time(7), max_session=timedelta(minutes=30))
    assert controls.decide(datetime(2026, 1, 15, 12, 1, tzinfo=timezone.utc), NOW)[0] == "ALLOWED"
    assert controls.decide(datetime(2026, 1, 15, 23, tzinfo=timezone.utc), NOW)[0] == "QUIET_HOURS"
    assert controls.decide(NOW + timedelta(minutes=30), NOW)[0] == "SESSION_LIMIT"
    assert controls.pause().decide(NOW, NOW)[0] == "PAUSED"


@pytest.mark.parametrize("text", ["chase losses", "win it back", "last chance", "act now", "urgent action"])
def test_chase_loss_and_urgency_cues_are_rejected(text: str) -> None:
    with pytest.raises(AnnotationExportError, match="prohibited"):
        validate_responsible_copy(text)


def test_reflection_copy_is_allowed() -> None:
    validate_responsible_copy("Pause and reflect on your time, reasons and evidence before continuing.")
