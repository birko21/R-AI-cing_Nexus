"""Official result revisions and selection reconciliation, kept separate from paper scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.contracts import Selection


ResultStatus = Literal["PENDING", "OFFICIAL", "CORRECTED"]
SelectionOutcome = Literal["PENDING", "PASS", "WIN", "PLACE", "LOSS", "SCRATCHED", "DEAD_HEAT", "VOID"]


class ResultReconciliationError(ValueError):
    """Raised when a result is not safe to reconcile."""


class OfficialResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    result_id: str = Field(min_length=1)
    race_id: str = Field(min_length=1)
    field_revision: str = Field(min_length=1)
    source_receipt_id: str = Field(min_length=1)
    status: ResultStatus
    observed_at: datetime
    official_at: datetime | None = None
    placings: dict[str, int]
    dead_heat_groups: tuple[tuple[str, ...], ...] = ()
    scratched_entries: frozenset[str] = frozenset()
    correction_of: str | None = None
    data_mode: Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]

    @model_validator(mode="after")
    def validate_result(self) -> OfficialResult:
        for field_name in ("observed_at", "official_at"):
            timestamp = getattr(self, field_name)
            if timestamp is not None and (timestamp.tzinfo is None or timestamp.utcoffset() is None):
                raise ResultReconciliationError(f"{field_name} must be timezone-aware")
        if self.status == "PENDING" and self.official_at is not None:
            raise ResultReconciliationError("pending results cannot have an official timestamp")
        if self.status in {"OFFICIAL", "CORRECTED"} and self.official_at is None:
            raise ResultReconciliationError("official results require an official timestamp")
        if self.status == "CORRECTED" and not self.correction_of:
            raise ResultReconciliationError("corrected results require correction_of")
        if any(position < 1 for position in self.placings.values()):
            raise ResultReconciliationError("placing positions must be positive")
        return self

    def outcome_for(self, entry_id: str) -> SelectionOutcome:
        if entry_id in self.scratched_entries:
            return "SCRATCHED"
        for group in self.dead_heat_groups:
            if entry_id in group:
                return "DEAD_HEAT"
        position = self.placings.get(entry_id)
        if position is None:
            return "VOID"
        return "WIN" if position == 1 else "PLACE" if position <= 3 else "LOSS"


@dataclass(frozen=True)
class SelectionReconciliation:
    selection_id: str
    result_id: str
    outcome: SelectionOutcome
    reconciled_at: datetime


class ResultRegistry:
    def __init__(self) -> None:
        self._results: dict[str, OfficialResult] = {}
        self._reconciliations: dict[tuple[str, str], SelectionReconciliation] = {}

    def append(self, result: OfficialResult) -> None:
        if result.result_id in self._results:
            raise ResultReconciliationError("result revisions are append-only")
        if result.correction_of is not None and result.correction_of not in self._results:
            raise ResultReconciliationError("correction must reference an existing result revision")
        self._results[result.result_id] = result

    def latest(self, race_id: str) -> OfficialResult | None:
        candidates = [result for result in self._results.values() if result.race_id == race_id and result.status in {"OFFICIAL", "CORRECTED"}]
        return max(candidates, key=lambda result: (result.observed_at, result.result_id), default=None)

    def reconcile(self, selection: Selection, result: OfficialResult, now: datetime | None = None) -> SelectionReconciliation:
        if result.status == "PENDING" or result.official_at is None:
            raise ResultReconciliationError("selection outcomes require an official result")
        if selection.race_id != result.race_id:
            raise ResultReconciliationError("selection and result race IDs do not match")
        key = (selection.selection_id, result.result_id)
        if key in self._reconciliations:
            raise ResultReconciliationError("selection reconciliation is append-only")
        outcome: SelectionOutcome = "PASS" if selection.selection_type == "PASS" else result.outcome_for(selection.entry_id or "")
        timestamp = now or datetime.now(timezone.utc)
        reconciliation = SelectionReconciliation(selection.selection_id, result.result_id, outcome, timestamp)
        self._reconciliations[key] = reconciliation
        return reconciliation

    def snapshot(self) -> dict[str, object]:
        return {
            "results": [result.model_dump(mode="json") for result in self._results.values()],
            "reconciliations": [item.__dict__ for item in self._reconciliations.values()],
            "paper_simulation_included": False,
            "model_rankings_included": False,
        }
