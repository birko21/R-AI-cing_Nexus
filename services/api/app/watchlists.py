"""Stable identity watchlists with append-only lifecycle events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


WatchKind = Literal["RUNNER", "RACE"]
WatchState = Literal["ACTIVE", "PAUSED", "REMOVED"]
WatchEventKind = Literal["CREATED", "IDENTITY_CHANGED", "SOURCE_CHANGED", "PAUSED", "RESUMED", "REMOVED"]


@dataclass(frozen=True)
class WatchTarget:
    watch_id: str
    entity_id: str
    kind: WatchKind
    code: str
    source_system: str
    source_id: str
    name: str
    state: WatchState


@dataclass(frozen=True)
class WatchEvent:
    event_id: str
    watch_id: str
    kind: WatchEventKind
    observed_at: datetime
    source_system: str
    source_id: str
    name: str
    detail: str


class WatchlistError(ValueError):
    pass


class WatchlistRegistry:
    def __init__(self) -> None:
        self._targets: dict[str, WatchTarget] = {}
        self._events: list[WatchEvent] = []
        self._next_watch = 1
        self._next_event = 1

    def create(self, entity_id: str, kind: WatchKind, code: str, source_system: str, source_id: str, name: str, now: datetime) -> WatchTarget:
        if not all(value.strip() for value in (entity_id, code, source_system, source_id, name)):
            raise WatchlistError("stable identity fields are required")
        self._require_time(now)
        watch_id = f"watch-{self._next_watch}"
        self._next_watch += 1
        target = WatchTarget(watch_id, entity_id, kind, code, source_system, source_id, name, "ACTIVE")
        self._targets[watch_id] = target
        self._event(target, "CREATED", now, "watch target created")
        return target

    def identity_change(self, watch_id: str, *, source_system: str, source_id: str, name: str, now: datetime, detail: str = "identity revision observed") -> WatchTarget:
        target = self._get_active(watch_id)
        self._require_time(now)
        updated = WatchTarget(target.watch_id, target.entity_id, target.kind, target.code, source_system, source_id, name, target.state)
        self._targets[watch_id] = updated
        event_kind: WatchEventKind = "SOURCE_CHANGED" if source_system != target.source_system else "IDENTITY_CHANGED"
        self._event(updated, event_kind, now, detail)
        return updated

    def pause(self, watch_id: str, now: datetime) -> WatchTarget:
        return self._state_change(watch_id, "PAUSED", "PAUSED", now)

    def resume(self, watch_id: str, now: datetime) -> WatchTarget:
        return self._state_change(watch_id, "ACTIVE", "RESUMED", now)

    def remove(self, watch_id: str, now: datetime) -> WatchTarget:
        return self._state_change(watch_id, "REMOVED", "REMOVED", now)

    def current(self, watch_id: str) -> WatchTarget:
        return self._targets.get(watch_id) or self._missing()

    def history(self, watch_id: str) -> list[WatchEvent]:
        self.current(watch_id)
        return [event for event in self._events if event.watch_id == watch_id]

    def _state_change(self, watch_id: str, state: WatchState, event_kind: WatchEventKind, now: datetime) -> WatchTarget:
        target = self._get_active(watch_id)
        self._require_time(now)
        if target.state == "REMOVED":
            raise WatchlistError("removed watch targets remain historical and cannot be changed")
        updated = WatchTarget(target.watch_id, target.entity_id, target.kind, target.code, target.source_system, target.source_id, target.name, state)
        self._targets[watch_id] = updated
        self._event(updated, event_kind, now, f"watch target {state.lower()}")
        return updated

    def _get_active(self, watch_id: str) -> WatchTarget:
        target = self._targets.get(watch_id)
        if target is None:
            return self._missing()
        return target

    def _event(self, target: WatchTarget, kind: WatchEventKind, now: datetime, detail: str) -> None:
        event = WatchEvent(f"watch-event-{self._next_event}", target.watch_id, kind, now, target.source_system, target.source_id, target.name, detail)
        self._next_event += 1
        self._events.append(event)

    @staticmethod
    def _require_time(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise WatchlistError("watchlist timestamps must be timezone-aware")

    @staticmethod
    def _missing() -> WatchTarget:
        raise WatchlistError("watch target was not found")
