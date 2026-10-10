from datetime import datetime, timezone

import pytest

from app.contracts import SelectionAddendumCreate, SelectionCreate
from app.selection_journal import SelectionJournal, SelectionJournalError


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def payload(selection_type: str = "WIN", **overrides: object) -> SelectionCreate:
    values: dict[str, object] = {
        "race_id": "THOROUGHBRED:fixture:race-1", "field_revision": "field-r2", "entry_id": "THOROUGHBRED:fixture:entry-1",
        "selection_type": selection_type, "rationale": "Fixture evidence is sufficient for a deliberate paper record.",
        "forecast_id": "forecast-1", "quote_id": "quote-1",
    }
    values.update(overrides)
    return SelectionCreate(**values)


def test_journal_captures_user_decision_field_and_references() -> None:
    journal = SelectionJournal()
    selection = journal.create("local-owner", payload(), NOW)

    assert selection.user_id == "local-owner"
    assert selection.decision_time == NOW
    assert selection.field_revision == "field-r2"
    assert selection.forecast_id == "forecast-1"
    assert selection.quote_id == "quote-1"


def test_pass_is_deliberate_and_can_omit_entry() -> None:
    selection = SelectionJournal().create("local-owner", payload("PASS", entry_id=None), NOW)
    assert selection.selection_type == "PASS"
    assert selection.entry_id is None


def test_non_pass_requires_exact_entry_and_corrections_are_addenda() -> None:
    journal = SelectionJournal()
    with pytest.raises(SelectionJournalError, match="entry_id"):
        journal.create("local-owner", payload(entry_id=None), NOW)
    selection = journal.create("local-owner", payload(), NOW)
    addendum = journal.addendum("local-owner", selection.selection_id, SelectionAddendumCreate(note="Corrected rationale; original remains unchanged."), NOW)

    assert addendum.selection_id == selection.selection_id
    assert journal.list_for_user("local-owner")[0].rationale.startswith("Fixture evidence")
    assert journal.addenda_for("local-owner", selection.selection_id) == [addendum]


def test_user_isolation_and_immutable_ids_are_enforced() -> None:
    journal = SelectionJournal()
    selection = journal.create("owner-a", payload(), NOW)
    with pytest.raises(SelectionJournalError, match="different user"):
        journal.addendum("owner-b", selection.selection_id, SelectionAddendumCreate(note="No cross-user mutation."), NOW)
    with pytest.raises(SelectionJournalError, match="not found"):
        journal.addendum("owner-a", "missing", SelectionAddendumCreate(note="Missing."), NOW)
