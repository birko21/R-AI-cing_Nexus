"""Append-only personal selection and PASS journal."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Engine, text

from app.contracts import Selection, SelectionAddendum, SelectionAddendumCreate, SelectionCreate


class SelectionJournalError(ValueError):
    """Raised when a personal journal operation violates an invariant."""


class SelectionJournal:
    def __init__(self) -> None:
        self._selections: dict[str, Selection] = {}
        self._addenda: list[SelectionAddendum] = []
        self._next_selection = 1
        self._next_addendum = 1

    def create(self, user_id: str, payload: SelectionCreate, now: datetime | None = None) -> Selection:
        if payload.selection_type != "PASS" and not payload.entry_id:
            raise SelectionJournalError("WIN and PLACE selections require an entry_id")
        timestamp = now or datetime.now(timezone.utc)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise SelectionJournalError("decision time must be timezone-aware")
        selection_id = f"selection-{self._next_selection}"
        self._next_selection += 1
        selection = Selection(
            **payload.model_dump(), selection_id=selection_id, user_id=user_id,
            created_at=timestamp, decision_time=timestamp, data_mode="SYNTHETIC_ONLY",
        )
        self._selections[selection_id] = selection
        return selection

    def list_for_user(self, user_id: str) -> list[Selection]:
        return [selection for selection in self._selections.values() if selection.user_id == user_id]

    def addendum(self, user_id: str, selection_id: str, payload: SelectionAddendumCreate, now: datetime | None = None) -> SelectionAddendum:
        selection = self._selections.get(selection_id)
        if selection is None:
            raise SelectionJournalError("selection was not found")
        if selection.user_id != user_id:
            raise SelectionJournalError("selection belongs to a different user")
        timestamp = now or datetime.now(timezone.utc)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise SelectionJournalError("addendum time must be timezone-aware")
        addendum = SelectionAddendum(
            **payload.model_dump(), addendum_id=f"addendum-{self._next_addendum}",
            selection_id=selection_id, user_id=user_id, created_at=timestamp,
        )
        self._next_addendum += 1
        self._addenda.append(addendum)
        return addendum

    def addenda_for(self, user_id: str, selection_id: str) -> list[SelectionAddendum]:
        return [item for item in self._addenda if item.user_id == user_id and item.selection_id == selection_id]


class PostgresSelectionJournal:
    """Append-only PostgreSQL journal with the same contract as the local journal."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def create(self, user_id: str, payload: SelectionCreate, now: datetime | None = None) -> Selection:
        if payload.selection_type != "PASS" and not payload.entry_id:
            raise SelectionJournalError("WIN and PLACE selections require an entry_id")
        timestamp = now or datetime.now(timezone.utc)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise SelectionJournalError("decision time must be timezone-aware")
        selection = Selection(
            **payload.model_dump(),
            selection_id=f"selection-{uuid4()}",
            user_id=user_id,
            created_at=timestamp,
            decision_time=timestamp,
            data_mode="SYNTHETIC_ONLY",
        )
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO personal_selections (
                        selection_id, user_id, race_id, field_revision, entry_id,
                        selection_type, rationale, forecast_id, quote_id,
                        created_at, decision_time, data_mode
                    ) VALUES (
                        :selection_id, :user_id, :race_id, :field_revision, :entry_id,
                        :selection_type, :rationale, :forecast_id, :quote_id,
                        :created_at, :decision_time, :data_mode
                    )
                    """
                ),
                selection.model_dump(mode="json"),
            )
        return selection

    def list_for_user(self, user_id: str) -> list[Selection]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT selection_id, user_id, race_id, field_revision, entry_id,
                           selection_type, rationale, forecast_id, quote_id,
                           created_at, decision_time, data_mode
                    FROM personal_selections
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC, selection_id
                    """
                ),
                {"user_id": user_id},
            ).mappings().all()
        return [Selection(**dict(row)) for row in rows]

    def addendum(self, user_id: str, selection_id: str, payload: SelectionAddendumCreate, now: datetime | None = None) -> SelectionAddendum:
        timestamp = now or datetime.now(timezone.utc)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise SelectionJournalError("addendum time must be timezone-aware")
        addendum = SelectionAddendum(
            **payload.model_dump(),
            addendum_id=f"addendum-{uuid4()}",
            selection_id=selection_id,
            user_id=user_id,
            created_at=timestamp,
        )
        with self.engine.begin() as connection:
            owner = connection.execute(
                text("SELECT user_id FROM personal_selections WHERE selection_id = :selection_id"),
                {"selection_id": selection_id},
            ).scalar_one_or_none()
            if owner is None:
                raise SelectionJournalError("selection was not found")
            if owner != user_id:
                raise SelectionJournalError("selection belongs to a different user")
            connection.execute(
                text(
                    """
                    INSERT INTO selection_addenda (addendum_id, selection_id, user_id, note, created_at)
                    VALUES (:addendum_id, :selection_id, :user_id, :note, :created_at)
                    """
                ),
                addendum.model_dump(mode="json"),
            )
        return addendum

    def addenda_for(self, user_id: str, selection_id: str) -> list[SelectionAddendum]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT addendum_id, selection_id, user_id, note, created_at
                    FROM selection_addenda
                    WHERE user_id = :user_id AND selection_id = :selection_id
                    ORDER BY created_at, addendum_id
                    """
                ),
                {"user_id": user_id, "selection_id": selection_id},
            ).mappings().all()
        return [SelectionAddendum(**dict(row)) for row in rows]
