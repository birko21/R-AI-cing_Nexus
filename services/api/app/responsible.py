"""Journal summaries, annotation-only export and responsible-use controls."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Literal

from app.contracts import Selection, SelectionAddendum


ControlStatus = Literal["ALLOWED", "PAUSED", "QUIET_HOURS", "SESSION_LIMIT"]

BLOCKED_CUE_PHRASES = ("chase losses", "win it back", "last chance", "act now", "don't miss out", "urgent")


@dataclass(frozen=True)
class JournalSummary:
    selection_count: int
    pass_count: int
    win_count: int
    place_count: int
    forecast_reference_count: int
    paper_simulation_included: bool = False

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def summarize_journal(selections: Iterable[Selection]) -> JournalSummary:
    items = list(selections)
    return JournalSummary(
        selection_count=len(items), pass_count=sum(item.selection_type == "PASS" for item in items),
        win_count=sum(item.selection_type == "WIN" for item in items), place_count=sum(item.selection_type == "PLACE" for item in items),
        forecast_reference_count=sum(item.forecast_id is not None for item in items),
    )


class AnnotationExportError(ValueError):
    pass


def export_annotations(selections: Iterable[Selection], addenda: Iterable[SelectionAddendum], *, permitted: bool) -> dict[str, object]:
    if not permitted:
        raise AnnotationExportError("annotation export is not permitted for this source or session")
    selection_items = list(selections)
    selection_ids = {item.selection_id for item in selection_items}
    addendum_items = [item for item in addenda if item.selection_id in selection_ids]
    return {
        "export_type": "ANNOTATIONS_ONLY",
        "data_mode": "SYNTHETIC_ONLY",
        "selections": [
            {"selection_id": item.selection_id, "race_id": item.race_id, "field_revision": item.field_revision,
             "selection_type": item.selection_type, "rationale": item.rationale, "decision_time": item.decision_time.isoformat()}
            for item in selection_items
        ],
        "addenda": [{"addendum_id": item.addendum_id, "selection_id": item.selection_id, "note": item.note, "created_at": item.created_at.isoformat()} for item in addendum_items],
        "raw_prices_included": False,
        "forecast_payloads_included": False,
    }


@dataclass(frozen=True)
class SessionControls:
    paused: bool = False
    quiet_hours_start: time = time(22, 0)
    quiet_hours_end: time = time(7, 0)
    max_session: timedelta = timedelta(minutes=60)

    def __post_init__(self) -> None:
        if self.max_session <= timedelta(0):
            raise ValueError("max_session must be positive")

    def decide(self, now: datetime, started_at: datetime) -> tuple[ControlStatus, str]:
        if now.tzinfo is None or now.utcoffset() is None or started_at.tzinfo is None or started_at.utcoffset() is None:
            raise ValueError("session control timestamps must be timezone-aware")
        if self.paused:
            return "PAUSED", "session is paused by the owner"
        current = now.timetz().replace(tzinfo=None)
        in_quiet = current >= self.quiet_hours_start or current < self.quiet_hours_end if self.quiet_hours_start > self.quiet_hours_end else self.quiet_hours_start <= current < self.quiet_hours_end
        if in_quiet:
            return "QUIET_HOURS", "quiet hours are active"
        if now - started_at >= self.max_session:
            return "SESSION_LIMIT", "session time limit reached; reflect before continuing"
        return "ALLOWED", "session is within the configured controls"

    def pause(self) -> SessionControls:
        return SessionControls(True, self.quiet_hours_start, self.quiet_hours_end, self.max_session)


def validate_responsible_copy(text: str) -> None:
    lowered = text.lower()
    blocked = [phrase for phrase in BLOCKED_CUE_PHRASES if phrase in lowered]
    if blocked:
        raise AnnotationExportError(f"urgency or chase-loss cue is prohibited: {', '.join(blocked)}")
