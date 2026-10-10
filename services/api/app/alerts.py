"""Confirmed, source-linked, deduplicated watchlist change alerts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


Validity = Literal["CONFIRMED", "UNCONFIRMED"]
AlertStatus = Literal["ACTIVE", "EXPIRED"]


@dataclass(frozen=True)
class ChangeEvent:
    event_id: str
    watch_id: str
    source_system: str
    source_receipt_id: str
    observed_at: datetime
    validity: Validity
    material: bool
    suppression_key: str
    cause: str
    expires_at: datetime


@dataclass(frozen=True)
class Alert:
    alert_id: str
    event_id: str
    watch_id: str
    source_system: str
    source_receipt_id: str
    observed_at: datetime
    suppression_key: str
    cause: str
    expires_at: datetime
    status: AlertStatus

    def to_dict(self) -> dict[str, object]:
        return {
            "alert_id": self.alert_id, "event_id": self.event_id, "watch_id": self.watch_id,
            "source_system": self.source_system, "source_receipt_id": self.source_receipt_id,
            "observed_at": self.observed_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "suppression_key": self.suppression_key, "cause": self.cause,
            "expires_at": self.expires_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": self.status,
        }


class AlertError(ValueError):
    pass


class AlertRouter:
    def __init__(self) -> None:
        self._events: dict[str, ChangeEvent] = {}
        self._alerts: dict[str, Alert] = {}
        self._by_suppression: dict[str, str] = {}
        self._next_alert = 1

    def ingest(self, event: ChangeEvent, now: datetime) -> Alert | None:
        self._validate_event(event, now)
        if event.event_id in self._events:
            raise AlertError("change events are append-only")
        self._events[event.event_id] = event
        if event.validity != "CONFIRMED" or not event.material or event.expires_at <= now:
            return None
        existing_id = self._by_suppression.get(event.suppression_key)
        if existing_id is not None:
            existing = self._alerts[existing_id]
            if existing.expires_at > now:
                return existing
        alert = Alert(
            alert_id=f"alert-{self._next_alert}", event_id=event.event_id, watch_id=event.watch_id,
            source_system=event.source_system, source_receipt_id=event.source_receipt_id,
            observed_at=event.observed_at, suppression_key=event.suppression_key, cause=event.cause,
            expires_at=event.expires_at, status="ACTIVE",
        )
        self._next_alert += 1
        self._alerts[alert.alert_id] = alert
        self._by_suppression[event.suppression_key] = alert.alert_id
        return alert

    def active_alerts(self, now: datetime) -> list[Alert]:
        self._require_time(now)
        return [self._status(alert, now) for alert in self._alerts.values() if alert.expires_at > now]

    def replay(self, events: list[ChangeEvent], now: datetime) -> list[Alert]:
        for event in events:
            self.ingest(event, now)
        return self.active_alerts(now)

    @staticmethod
    def _validate_event(event: ChangeEvent, now: datetime) -> None:
        AlertRouter._require_time(now)
        if not all(value.strip() for value in (event.event_id, event.watch_id, event.source_system, event.source_receipt_id, event.suppression_key, event.cause)):
            raise AlertError("source-linked event fields are required")
        for value in (event.observed_at, event.expires_at):
            AlertRouter._require_time(value)
        if event.expires_at <= event.observed_at:
            raise AlertError("alert expiry must follow observation")

    @staticmethod
    def _require_time(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise AlertError("alert timestamps must be timezone-aware")

    @staticmethod
    def _status(alert: Alert, now: datetime) -> Alert:
        return Alert(**{**alert.__dict__, "status": "ACTIVE" if alert.expires_at > now else "EXPIRED"})
